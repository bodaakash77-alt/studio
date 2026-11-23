"""Blender 4.x / 5.x script: 9:16 1080x1920 cinematic test scene.
Run:  blender -b -P toolkit/blender/blender_script.py -- --preset push_in --out render.png --samples 32 --res 1080x1920
Presets: push_in, pull_out, orbit, crane, drone, top_down
Engine: EEVEE if available, falls back to Cycles (CPU) on headless machines.
"""
import bpy, math, sys, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--preset', default='push_in')
ap.add_argument('--out', default='render.png')
ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--res', default='1080x1920')
ap.add_argument('--frame', type=int, default=0, help='0 = single still')
args = ap.parse_args(argv)
W, H = map(int, args.res.lower().split('x'))

PRESETS = {  # (frame, camera location, look-at point)
    'push_in':  [(1, (0, -12, 2.2), (0, 0, 1.4)), (120, (0, -6.5, 1.9), (0, 0, 1.4))],
    'pull_out': [(1, (0, -5, 1.6), (0, 0, 1.4)), (120, (0, -14, 3.4), (0, 0, 1.2))],
    'orbit':    [(1, (-9, -6, 3), (0, 0, 1)), (120, (9, -6, 3), (0, 0, 1))],
    'crane':    [(1, (0, -8, 0.8), (0, 0, 1.5)), (120, (0, -8, 7), (0, 0, 2))],
    'drone':    [(1, (-18, -22, 14), (0, 0, 2)), (120, (12, -10, 9), (0, 0, 2))],
    'top_down': [(1, (0, 0.01, 40), (0, 0, 0)), (120, (0, 0.01, 40), (0, 0, 0))],
}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.render.fps = 30
sc.view_settings.view_transform = 'AgX'
sc.view_settings.exposure = -0.4
try:
    sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = args.samples
except Exception:
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = args.samples
    sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True

def mat(name, col, rough=0.6, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*col, 1)
        b.inputs['Emission Strength'].default_value = emit
    return m

def add(kind, loc, scale=(1, 1, 1), m=None, **kw):
    getattr(bpy.ops.mesh, f'primitive_{kind}_add')(location=loc, **kw)
    o = bpy.context.object; o.scale = scale
    if m: o.data.materials.append(m)
    return o

# ---- ground and hill ----
add('plane', (0, 0, 0), (30, 30, 1), mat('grass', (0.25, 0.42, 0.18), 0.9))
add('ico_sphere', (0, 6, -6), (9, 6, 4), mat('hill', (0.3, 0.45, 0.2), 0.9), subdivisions=4)

# ---- clear water pool with shader (transmission + absorption + ripple bump) ----
water = add('plane', (-3.5, -1.5, 0.02), (2.2, 2.2, 1), None)
wm = bpy.data.materials.new('clear_water'); wm.use_nodes = True
n = wm.node_tree.nodes; l = wm.node_tree.links
b = n['Principled BSDF']
b.inputs['Base Color'].default_value = (0.7, 0.95, 0.9, 1)
b.inputs['Roughness'].default_value = 0.03
b.inputs['IOR'].default_value = 1.33
try: b.inputs['Transmission Weight'].default_value = 1.0
except Exception: pass
nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 6
bm = n.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.12
l.new(nz.outputs['Fac'], bm.inputs['Height']); l.new(bm.outputs['Normal'], b.inputs['Normal'])
water.data.materials.append(wm)

# ---- character placeholder: red helmet, green visor, red T-shirt, blue jeans, red shoes ----
char_loc = Vector((0.4, 0.5, 0))
add('cylinder', char_loc + Vector((0, 0, 0.4)), (0.18, 0.18, 0.4), mat('jeans', (0.1, 0.2, 0.55), 0.7))          # legs
add('cube', char_loc + Vector((0, 0, 1.25)), (0.42, 0.25, 0.5), mat('shirt', (0.8, 0.08, 0.08), 0.6))          # torso (red tee)
add('uv_sphere', char_loc + Vector((0, 0, 2.0)), (0.25, 0.25, 0.27), mat('skin', (0.75, 0.55, 0.42), 0.6))       # head
add('uv_sphere', char_loc + Vector((0, 0, 2.12)), (0.29, 0.29, 0.25), mat('helmet', (0.85, 0.05, 0.05), 0.35))   # red helmet
add('cube', char_loc + Vector((0, -0.23, 2.02)), (0.22, 0.04, 0.07), mat('visor', (0.1, 0.9, 0.3), 0.1, emit=0.3))  # green visor
for x in (-0.1, 0.1):
    add('cube', char_loc + Vector((x, 0.05, 0.05)), (0.1, 0.2, 0.05), mat('shoe', (0.8, 0.05, 0.05), 0.5))      # red shoes

# ---- sky, sun, soft fill (sunset-style warm key) ----
wd = bpy.data.worlds.new('World'); sc.world = wd; wd.use_nodes = True
nt = wd.node_tree
sk = nt.nodes.new('ShaderNodeTexSky'); sk.sky_type = 'MULTIPLE_SCATTERING'
sk.sun_elevation = math.radians(12); sk.sun_rotation = math.radians(200)
nt.links.new(sk.outputs['Color'], nt.nodes['Background'].inputs['Color'])
nt.nodes['Background'].inputs['Strength'].default_value = 0.35
sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 3.0; sun.angle = math.radians(1.5)
so = bpy.data.objects.new('Sun', sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(70), 0, math.radians(120))

# ---- camera with Bezier push/pull/orbit keys ----
cam_d = bpy.data.cameras.new('Cam'); cam_d.lens = 35; cam_d.dof.use_dof = True
cam_d.dof.aperture_fstop = 5.6; cam_d.dof.focus_distance = 8
cam = bpy.data.objects.new('Cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new('Target', None); sc.collection.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
(f0, p0, l0), (f1, p1, l1) = PRESETS[args.preset]
try: bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
except Exception: pass
for f, p, look in ((f0, p0, l0), (f1, p1, l1)):
    cam.location = p; cam.keyframe_insert('location', frame=f)
    tgt.location = look; tgt.keyframe_insert('location', frame=f)
sc.frame_start, sc.frame_end = 1, 120
sc.frame_set(args.frame or 1)
sc.render.filepath = args.out
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print('DONE', args.out, sc.render.engine, W, H)
