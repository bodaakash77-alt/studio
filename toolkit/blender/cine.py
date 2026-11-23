"""Reusable cinematic helpers for bpy (Blender 5.x). Import from a scene script:
    import sys; sys.path.insert(0,'/home/claude/studio/toolkit/blender'); import cine
"""
import bpy, math
from mathutils import Vector

CAMERA_PRESETS = {
    # name: list of (t, location, look_at) keys in seconds
    "push_in":     [(0, (0, -12, 2.5), (0, 0, 1.5)), (6, (0, -7, 2.0), (0, 0, 1.5))],
    "pull_out":    [(0, (0, -5, 1.8), (0, 0, 1.5)), (6, (0, -13, 3.5), (0, 0, 1.5))],
    "orbit":       [(0, (-9, -6, 3), (0, 0, 1)), (8, (9, -6, 3), (0, 0, 1))],
    "crane_up":    [(0, (0, -8, 0.8), (0, 0, 1.5)), (7, (0, -8, 7), (0, 0, 2))],
    "drone_fly":   [(0, (-18, -22, 14), (0, 0, 2)), (10, (12, -10, 9), (0, 0, 2))],
    "top_down":    [(0, (0, 0, 40), (0, 0.01, 0))],
}

def set_cinematic_defaults(scene, samples=64, res=(1080, 1920), exposure=-0.5):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = exposure
    scene.render.fps = 30

def add_camera(name, lens=35, fstop=None, focus=None):
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    if fstop:
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = fstop
        cam_data.dof.focus_distance = focus or 10
    return cam

def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def keyframe_preset(cam, preset, speed=1.0):
    """Keys the camera location and look-at target with Bezier easing."""
    keys = CAMERA_PRESETS[preset]
    fps = bpy.context.scene.render.fps
    target = bpy.data.objects.new(f"{cam.name}_target", None)
    bpy.context.scene.collection.objects.link(target)
    con = cam.constraints.new('TRACK_TO')
    con.target = target; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    for t, loc, look in keys:
        f = int(t / speed * fps) + 1
        cam.location = loc; cam.keyframe_insert('location', frame=f)
        target.location = look; target.keyframe_insert('location', frame=f)
    if cam.animation_data and cam.animation_data.action:
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    return target

def ocean_like_water(obj):
    """Clear-water shader: transmission, slight absorption, bump ripples."""
    m = bpy.data.materials.new('clear_water'); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links
    b = n['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.7, 0.95, 0.9, 1)
    b.inputs['Roughness'].default_value = 0.03
    b.inputs['Transmission Weight'].default_value = 1
    b.inputs['IOR'].default_value = 1.33
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 6
    bm = n.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.12; bm.inputs['Distance'].default_value = 0.3
    l.new(nz.outputs['Fac'], bm.inputs['Height']); l.new(bm.outputs['Normal'], b.inputs['Normal'])
    vol = n.new('ShaderNodeVolumeAbsorption'); vol.inputs['Color'].default_value = (0.55, 0.95, 0.8, 1); vol.inputs['Density'].default_value = 0.25
    l.new(vol.outputs['Volume'], n['Material Output'].inputs['Volume'])
    obj.data.materials.append(m)
    return m

def sky_sun(elevation_deg=48, rotation_deg=200, strength=0.35, sun_energy=2.2):
    wd = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
    bpy.context.scene.world = wd; wd.use_nodes = True
    nt = wd.node_tree
    sk = nt.nodes.new('ShaderNodeTexSky'); sk.sky_type = 'MULTIPLE_SCATTERING'
    sk.sun_elevation = math.radians(elevation_deg); sk.sun_rotation = math.radians(rotation_deg)
    nt.links.new(sk.outputs['Color'], nt.nodes['Background'].inputs['Color'])
    nt.nodes['Background'].inputs['Strength'].default_value = strength
    sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = sun_energy
    so = bpy.data.objects.new('Sun', sun); bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(elevation_deg), 0, math.radians(rotation_deg / 10))
    return so
