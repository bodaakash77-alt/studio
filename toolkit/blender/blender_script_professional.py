"""Professional map-video scene builder for Blender 4.2+ (EEVEE Next) and 5.x.

Builds a 3D extruded world map (Lambert azimuthal equal-area, centred on Greenland) from the
library's Natural Earth data, lights it with a library HDRI, and animates the camera per scene
from projects/greenland/scene.json. MAP scenes only: no characters, no placeholder primitives.

Examples
  Preview stills (one per scene):
    blender -b -P blender_script_professional.py -- --still --res 540x960 --samples 16 --out /content/preview
  Full frames (slow; see --frame-step and --engine cycles for GPU):
    blender -b -P blender_script_professional.py -- --res 1080x1920 --samples 32 --out /content/frames

Library files (map, HDRI, scene.json) are read from the repo checkout if present, otherwise
downloaded from GitHub at --ref (a commit SHA keeps the download immutable and un-cached).
"""
import bpy, bmesh, math, sys, os, json, random, argparse, urllib.request
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--scene-json', default='projects/greenland/scene.json')
ap.add_argument('--ref', default='main', help='GitHub commit SHA/branch for downloads')
ap.add_argument('--repo', default='bodaakash77-alt/studio')
ap.add_argument('--cache', default=os.path.join(os.path.expanduser('~'), '.studio_cache'))
ap.add_argument('--hdri', default='dawn')
ap.add_argument('--res', default='1080x1920')
ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--engine', default='eevee', choices=['eevee', 'cycles'])
ap.add_argument('--out', default='render_out')
ap.add_argument('--still', action='store_true', help='render the middle frame of every scene')
ap.add_argument('--only-scene', type=int, default=0)
ap.add_argument('--frame-start', type=int, default=0)
ap.add_argument('--frame-end', type=int, default=0)
ap.add_argument('--frame-step', type=int, default=1)
ap.add_argument('--no-glow', action='store_true')
ap.add_argument('--save-blend', default='')
args = ap.parse_args(argv)
W, H = map(int, args.res.lower().split('x'))
FPS = 30

# ---------------------------------------------------------------- files
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

def repo_file(rel):
    """Local repo file if present, else download from GitHub raw at --ref."""
    local = os.path.join(REPO_ROOT, rel)
    if os.path.exists(local):
        return local
    dest = os.path.join(args.cache, args.ref, rel)
    if not os.path.exists(dest):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        url = f'https://raw.githubusercontent.com/{args.repo}/{args.ref}/{rel}'
        print('downloading', url)
        urllib.request.urlretrieve(url, dest)
    return dest

SCENES = json.load(open(repo_file(args.scene_json), encoding='utf-8'))
TOTAL_FRAMES = int(round(SCENES['scenes'][-1]['end_time'] * FPS))

# ---------------------------------------------------------------- map data + projection
LAT0, LON0 = math.radians(72.0), math.radians(-42.0)   # projection centre (Greenland)
R_UNITS = 6371.0 / 250.0                               # 1 Blender unit = 250 km

def proj(lat, lon):
    """Lambert azimuthal equal-area. Returns (x, y, cos_c); cos_c < -0.25 means far side of Earth."""
    p, l = math.radians(lat), math.radians(lon)
    dl = l - LON0
    cos_c = math.sin(LAT0) * math.sin(p) + math.cos(LAT0) * math.cos(p) * math.cos(dl)
    k = math.sqrt(2.0 / max(1e-9, 1.0 + cos_c))
    x = R_UNITS * k * math.cos(p) * math.sin(dl)
    y = R_UNITS * k * (math.cos(LAT0) * math.sin(p) - math.sin(LAT0) * math.cos(p) * math.cos(dl))
    return x, y, cos_c

def load_countries(path, wanted):
    topo = json.load(open(path))
    sc, tr = topo['transform']['scale'], topo['transform']['translate']
    arcs = []
    for a in topo['arcs']:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx; y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)
    def ring(idx):
        pts = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a if not pts else a[1:])
        return pts
    out = {}
    for g in topo['objects']['countries']['geometries']:
        try:
            iso = int(g.get('id'))
        except (TypeError, ValueError):
            continue
        if iso not in wanted:
            continue
        polys = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]
        out[iso] = {'name': g['properties']['name'], 'rings': [ring(p[0]) for p in polys]}
    return out

def project_ring(ll, tol):
    pts = []
    for lon, lat in ll:
        x, y, c = proj(lat, lon)
        if c < -0.25:
            return None
        if not pts or math.hypot(x - pts[-1][0], y - pts[-1][1]) >= tol:
            pts.append((x, y))
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    if len(pts) < 3:
        return None
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if area > 0 else pts[::-1]

# ---------------------------------------------------------------- helpers
def interp(kind):
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = kind
    except Exception:
        pass

def setin(node, name, value):
    try:
        node.inputs[name].default_value = value
    except (KeyError, TypeError):
        pass

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    for n in list(m.node_tree.nodes):
        m.node_tree.nodes.remove(n)
    return m, m.node_tree.nodes, m.node_tree.links

def principled(nodes, color, rough=0.5, emit=None, emit_strength=0.0):
    b = nodes.new('ShaderNodeBsdfPrincipled')
    setin(b, 'Base Color', (*color, 1))
    setin(b, 'Roughness', rough)
    if emit is not None:
        setin(b, 'Emission Color', (*emit, 1))
        setin(b, 'Emission Strength', emit_strength)
    return b

def emission_mat(name, color, strength):
    m, n, l = new_mat(name)
    e = n.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    o = n.new('ShaderNodeOutputMaterial'); l.new(e.outputs[0], o.inputs[0])
    return m, e

def poly_curve(name, pts3, mat, bevel, cyclic=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = 1
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts3) - 1)
    for p, c in zip(sp.points, pts3):
        p.co = (c[0], c[1], c[2], 1)
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(mat)
    return ob, cu

def fill_disc(name, cx, cy, z, r, mat, seg=24):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg), z)) for i in range(seg)]
    bm.faces.new(vs)
    bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = (0, 0, 0)
    bpy.context.scene.collection.objects.link(ob)
    return ob

def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside

# ---------------------------------------------------------------- scene setup
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, TOTAL_FRAMES
sc.view_settings.view_transform = 'AgX'
for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
    try:
        sc.view_settings.look = look
        break
    except TypeError:
        pass
sc.view_settings.exposure = -0.2

if args.engine == 'cycles':
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = args.samples
    sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for dev_type in ('OPTIX', 'CUDA'):
            try:
                prefs.compute_device_type = dev_type
                prefs.get_devices()
                if any(d.type != 'CPU' for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = True
                    sc.cycles.device = 'GPU'
                    break
            except Exception:
                continue
    except Exception:
        pass
else:
    ids = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in ids else 'BLENDER_EEVEE'
    try:
        sc.eevee.taa_render_samples = args.samples
    except Exception:
        pass
    try:
        sc.eevee.use_raytracing = True
    except Exception:
        pass

# ---------------------------------------------------------------- world: library HDRI
wd = bpy.data.worlds.new('World'); sc.world = wd; wd.use_nodes = True
wn, wl = wd.node_tree.nodes, wd.node_tree.links
bg = wn['Background']
try:
    env = wn.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(repo_file(f'library/core/hdri/{args.hdri}.exr'))
    wl.new(env.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.9
except Exception as e:
    print('HDRI load failed, using flat sky:', e)
    bg.inputs['Color'].default_value = (0.35, 0.45, 0.6, 1)
sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 3.5; sun.angle = math.radians(2.0); sun.color = (0.85, 0.92, 1.0)
so = bpy.data.objects.new('Sun', sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(55), 0, math.radians(35))

# ---------------------------------------------------------------- ocean
ocean_me = bpy.data.meshes.new('Ocean')
bm = bmesh.new(); S = 320
vs = [bm.verts.new(v) for v in ((-S, -S, -0.04), (S, -S, -0.04), (S, S, -0.04), (-S, S, -0.04))]
bm.faces.new(vs); bm.to_mesh(ocean_me); bm.free()
ocean = bpy.data.objects.new('Ocean', ocean_me); sc.collection.objects.link(ocean)
om, on, ol = new_mat('ocean')
ob_ = principled(on, (0.012, 0.045, 0.08), 0.1)
setin(ob_, 'Specular IOR Level', 0.6)
oc_tc = on.new('ShaderNodeTexCoord'); onz = on.new('ShaderNodeTexNoise'); onz.noise_dimensions = '4D'
onz.inputs['Scale'].default_value = 0.7; onz.inputs['Detail'].default_value = 6
obump = on.new('ShaderNodeBump'); obump.inputs['Strength'].default_value = 0.08
ol.new(oc_tc.outputs['Object'], onz.inputs['Vector']); ol.new(onz.outputs['Fac'], obump.inputs['Height'])
ol.new(obump.outputs['Normal'], ob_.inputs['Normal'])
oout = on.new('ShaderNodeOutputMaterial'); ol.new(ob_.outputs[0], oout.inputs[0])
interp('LINEAR')
onz.inputs['W'].default_value = 0.0; onz.inputs['W'].keyframe_insert('default_value', frame=1)
onz.inputs['W'].default_value = 4.0; onz.inputs['W'].keyframe_insert('default_value', frame=TOTAL_FRAMES)
ocean_me.materials.append(om)

# ---------------------------------------------------------------- land
WANTED = {304, 124, 840, 352, 578, 752, 246, 643, 208, 826, 372, 276, 616, 250, 724, 620, 528, 56, 756, 40, 203,
          703, 348, 642, 100, 804, 112, 440, 428, 233, 380, 300, 792, 398, 496, 156, 392, 408, 410, 484, 192, 304}
countries = load_countries(repo_file('library/core/maps/countries-10m.json'), WANTED)
border_mat, _ = emission_mat('border', (0.55, 0.72, 0.85), 0.9)
coast_mat, coast_emit = emission_mat('greenland_coast', (0.75, 0.9, 1.0), 2.0)
land_emit = {}   # iso -> (principled node)
GREENLAND_POLYS = []
objs_land = {}

def build_land(iso, c):
    tol = 0.003 if iso == 304 else 0.02
    me = bpy.data.meshes.new(c['name']); bm = bmesh.new(); polys = []
    for ll in c['rings']:
        pts = project_ring(ll, tol)
        if not pts:
            continue
        polys.append(pts)
        try:
            bm.faces.new([bm.verts.new((x, y, 0.0)) for x, y in pts])
        except ValueError:
            pass
    if not bm.faces:
        bm.free(); return None, []
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='EAR_CLIP')
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(c['name'], me); sc.collection.objects.link(ob)
    md = ob.modifiers.new('Solid', 'SOLIDIFY'); md.thickness = 0.07 if iso == 304 else 0.04; md.offset = 1.0
    return ob, polys

for iso, c in countries.items():
    ob, polys = build_land(iso, c)
    if ob is None:
        continue
    objs_land[iso] = ob
    if iso == 304:
        GREENLAND_POLYS = polys
        # ice sheet shader with animatable melt threshold
        m, n, l = new_mat('ice')
        ice = principled(n, (0.85, 0.93, 1.0), 0.38)
        setin(ice, 'Subsurface Weight', 0.25); setin(ice, 'Subsurface Radius', (0.4, 0.6, 1.0))
        rock = principled(n, (0.07, 0.06, 0.055), 0.9)
        tc = n.new('ShaderNodeTexCoord')
        nbig = n.new('ShaderNodeTexNoise'); nbig.inputs['Scale'].default_value = 0.9; nbig.inputs['Detail'].default_value = 8
        ramp = n.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.25; ramp.color_ramp.elements[0].color = (0.62, 0.78, 0.92, 1)
        ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        nfine = n.new('ShaderNodeTexNoise'); nfine.inputs['Scale'].default_value = 18; nfine.inputs['Detail'].default_value = 14
        bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.05
        nmelt = n.new('ShaderNodeTexNoise'); nmelt.inputs['Scale'].default_value = 1.6; nmelt.inputs['Detail'].default_value = 7
        sub = n.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
        mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 10.0; mul.use_clamp = True
        mix = n.new('ShaderNodeMixShader')
        o = n.new('ShaderNodeOutputMaterial')
        l.new(tc.outputs['Object'], nbig.inputs['Vector']); l.new(tc.outputs['Object'], nfine.inputs['Vector']); l.new(tc.outputs['Object'], nmelt.inputs['Vector'])
        l.new(nbig.outputs['Fac'], ramp.inputs['Fac']); l.new(ramp.outputs['Color'], ice.inputs['Base Color'])
        l.new(nfine.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs['Normal'], ice.inputs['Normal'])
        l.new(nmelt.outputs['Fac'], sub.inputs[0]); sub.inputs[1].default_value = 0.0
        l.new(sub.outputs[0], mul.inputs[0])
        l.new(mul.outputs[0], mix.inputs[0])   # factor 1 = ice, 0 = bare rock
        l.new(rock.outputs[0], mix.inputs[1]); l.new(ice.outputs[0], mix.inputs[2])
        l.new(mix.outputs[0], o.inputs[0])
        ob.data.materials.append(m)
        MELT_SOCKET = sub.inputs[1]
        # bright coastline
        for pts in polys:
            if len(pts) > 40:
                poly_curve('coast', [(x, y, 0.075) for x, y in pts], coast_mat, 0.022, True)
    else:
        m, n, l = new_mat(f'land_{iso}')
        b = principled(n, (0.055, 0.078, 0.095), 0.85, emit=(0.0, 0.0, 0.0), emit_strength=0.0)
        o = n.new('ShaderNodeOutputMaterial'); l.new(b.outputs[0], o.inputs[0])
        ob.data.materials.append(m)
        land_emit[iso] = b
        for pts in polys:
            if len(pts) > 30:
                poly_curve('border', [(x, y, 0.045) for x, y in pts], border_mat, 0.01, True)

# graticule
grat_mat, _ = emission_mat('graticule', (0.25, 0.45, 0.6), 0.25)
for lat in range(30, 90, 10):
    pts = []
    for lon in range(-180, 181, 3):
        x, y, c = proj(lat, lon)
        if c > -0.2:
            pts.append((x, y, -0.02))
    if len(pts) > 2:
        poly_curve('parallel', pts, grat_mat, 0.012)
for lon in range(-180, 180, 30):
    pts = []
    for lat in range(20, 90, 2):
        x, y, c = proj(lat, lon)
        if c > -0.2:
            pts.append((x, y, -0.02))
    if len(pts) > 2:
        poly_curve('meridian', pts, grat_mat, 0.012)

# ---------------------------------------------------------------- camera
cam_d = bpy.data.cameras.new('MapCam'); cam_d.lens = 35; cam_d.sensor_fit = 'VERTICAL'; cam_d.sensor_height = 36
cam = bpy.data.objects.new('MapCam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new('Target', None); sc.collection.objects.link(tgt)
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = tgt; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
cam_d.dof.use_dof = True; cam_d.dof.focus_object = tgt; cam_d.dof.aperture_fstop = 5.6

def cam_pose(lat, lon, dist, tilt, az):
    fx, fy, _ = proj(lat, lon)
    t, a = math.radians(max(tilt, 1.5)), math.radians(az)
    return Vector((fx + dist * math.sin(t) * math.sin(a), fy - dist * math.sin(t) * math.cos(a), dist * math.cos(t))), Vector((fx, fy, 0.0))

def key_obj(ob, prop, frame, kind):
    interp(kind)
    ob.keyframe_insert(prop, frame=frame)

# ---------------------------------------------------------------- per-scene animation
def frames_of(s):
    return int(round(s['start_time'] * FPS)) + 1, int(round(s['end_time'] * FPS))

treasure_made = False
for s in SCENES['scenes']:
    f0, f1 = frames_of(s)
    c = s['camera']
    for frame, (lat, lon), dist, kind in ((f0, c['focus_from'], c['dist_from'], 'BEZIER'), (f1, c['focus_to'], c['dist_to'], 'CONSTANT')):
        pos, look = cam_pose(lat, lon, dist, c['tilt_deg'], c['azimuth_deg'])
        cam.location = pos; tgt.location = look
        key_obj(cam, 'location', frame, kind); key_obj(tgt, 'location', frame, kind)
    for e in s.get('effects', []):
        t = e['type']
        if t == 'highlight' and e['iso'] in land_emit:
            b = land_emit[e['iso']]
            setin(b, 'Emission Color', (*e['color'], 1))
            for fr, v, k in ((f0 - 1, 0.0, 'BEZIER'), (f0 + 15, e['strength'], 'BEZIER'), (f1 - 10, e['strength'], 'BEZIER'), (f1, 0.0, 'CONSTANT')):
                b.inputs['Emission Strength'].default_value = v
                interp(k); b.inputs['Emission Strength'].keyframe_insert('default_value', frame=max(1, fr))
        elif t == 'arc':
            x0, y0, _ = proj(*e['from']); x1, y1, _ = proj(*e['to'])
            pts = [(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, 0.1 + e['height'] * math.sin(math.pi * u)) for u in [i / 80 for i in range(81)]]
            am, _ = emission_mat(f'arc_s{s["id"]}', tuple(e['color']), 5.0)
            ob, cu = poly_curve(f'arc_s{s["id"]}', pts, am, 0.06)
            cu.bevel_factor_start = 0.0
            cu.bevel_factor_end = 0.0; interp('BEZIER'); cu.keyframe_insert('bevel_factor_end', frame=f0 + 10)
            cu.bevel_factor_end = 1.0; interp('BEZIER'); cu.keyframe_insert('bevel_factor_end', frame=min(f1 - 20, f0 + 70))
            cu.bevel_factor_end = 1.0; interp('CONSTANT'); cu.keyframe_insert('bevel_factor_end', frame=f1)
            cu.bevel_factor_end = 0.0; cu.keyframe_insert('bevel_factor_end', frame=f1 + 1)
        elif t == 'markers':
            mm, me_ = emission_mat(f'marker_s{s["id"]}', tuple(e['color']), 6.0)
            for i, (lat, lon) in enumerate(e['points']):
                x, y, _ = proj(lat, lon)
                ring = [(x + 0.28 * math.cos(2 * math.pi * k / 40), y + 0.28 * math.sin(2 * math.pi * k / 40), 0.13) for k in range(40)]
                ob, cu = poly_curve(f'marker_s{s["id"]}_{i}', ring, mm, 0.035, True)
                ob.location = (x, y, 0); ob.data.transform(__import__('mathutils').Matrix.Translation((-x, -y, 0)))
                ob.scale = (0.0, 0.0, 0.0); key_obj(ob, 'scale', max(1, f0 - 1), 'BEZIER')
                start = f0 + 8 + i * 6
                step = 28
                fr = start; up = True
                while fr < f1:
                    sv = 1.0 if up else 1.9
                    ob.scale = (sv, sv, sv); key_obj(ob, 'scale', fr, 'BEZIER')
                    up = not up; fr += step
                ob.scale = (1.0, 1.0, 1.0); key_obj(ob, 'scale', f1, 'CONSTANT')
                ob.scale = (0.0, 0.0, 0.0); key_obj(ob, 'scale', f1 + 1, 'CONSTANT')
        elif t == 'melt':
            MELT_SOCKET.default_value = 0.0; interp('BEZIER'); MELT_SOCKET.keyframe_insert('default_value', frame=max(1, f0 - 1))
            MELT_SOCKET.default_value = 0.72; interp('BEZIER'); MELT_SOCKET.keyframe_insert('default_value', frame=f1 - 6)
            MELT_SOCKET.default_value = 0.72; interp('CONSTANT'); MELT_SOCKET.keyframe_insert('default_value', frame=f1)
            MELT_SOCKET.default_value = 0.0; MELT_SOCKET.keyframe_insert('default_value', frame=f1 + 1)
        elif t == 'treasure' and GREENLAND_POLYS:
            rnd = random.Random(7)
            main = max(GREENLAND_POLYS, key=len)
            xs = [p[0] for p in main]; ys = [p[1] for p in main]
            gm, ge = emission_mat('treasure', (1.0, 0.62, 0.12), 9.0)
            made = 0
            while made < e['count']:
                x, y = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))
                if not point_in_poly(x, y, main):
                    continue
                r = rnd.uniform(0.07, 0.15)
                d = fill_disc(f'ore_{made}', 0, 0, 0.11, r, gm)
                d.location = (x, y, 0)
                d.scale = (0, 0, 0); key_obj(d, 'scale', max(1, f0 - 1), 'BEZIER')
                grow = f0 + 12 + int(rnd.random() * (f1 - f0 - 40))
                d.scale = (0, 0, 0); key_obj(d, 'scale', grow, 'BEZIER')
                d.scale = (1, 1, 1); key_obj(d, 'scale', grow + 14, 'BEZIER')
                d.scale = (1.35, 1.35, 1.35); key_obj(d, 'scale', grow + 30, 'BEZIER')
                d.scale = (1, 1, 1); key_obj(d, 'scale', f1, 'CONSTANT')
                d.scale = (0, 0, 0); key_obj(d, 'scale', f1 + 1, 'CONSTANT')
                made += 1
        elif t == 'coastglow':
            coast_emit.inputs['Strength'].default_value = 2.0; interp('BEZIER'); coast_emit.inputs['Strength'].keyframe_insert('default_value', frame=max(1, f0 - 1))
            coast_emit.inputs['Strength'].default_value = 9.0; coast_emit.inputs['Strength'].keyframe_insert('default_value', frame=f0 + 45)
            coast_emit.inputs['Strength'].default_value = 5.0; interp('CONSTANT'); coast_emit.inputs['Strength'].keyframe_insert('default_value', frame=f1)

# ---------------------------------------------------------------- glow (compositor), best effort
if not args.no_glow:
    try:
        sc.use_nodes = True
        nt = sc.node_tree
        for n_ in list(nt.nodes):
            nt.nodes.remove(n_)
        rl = nt.nodes.new('CompositorNodeRLayers'); gl = nt.nodes.new('CompositorNodeGlare')
        gl.glare_type = 'FOG_GLOW'; gl.quality = 'MEDIUM'; gl.threshold = 1.0; gl.mix = -0.7
        co = nt.nodes.new('CompositorNodeComposite')
        nt.links.new(rl.outputs['Image'], gl.inputs['Image']); nt.links.new(gl.outputs['Image'], co.inputs['Image'])
    except Exception as ex:
        print('glow skipped:', ex)

# ---------------------------------------------------------------- render
os.makedirs(args.out, exist_ok=True)
sc.render.image_settings.file_format = 'PNG'
if args.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=args.save_blend)
if args.still:
    for s in SCENES['scenes']:
        if args.only_scene and s['id'] != args.only_scene:
            continue
        f0, f1 = frames_of(s)
        sc.frame_set((f0 + f1) // 2)
        sc.render.filepath = os.path.join(args.out, f'preview_scene{s["id"]:02d}.png')
        bpy.ops.render.render(write_still=True)
        print('STILL', sc.render.filepath)
else:
    sc.frame_start = args.frame_start or 1
    sc.frame_end = args.frame_end or TOTAL_FRAMES
    sc.frame_step = args.frame_step
    sc.render.filepath = os.path.join(args.out, 'frame_')
    bpy.ops.render.render(animation=True)
print('DONE', sc.render.engine, W, H)
