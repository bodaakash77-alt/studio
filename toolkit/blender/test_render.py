import bpy, sys
sys.path.insert(0,'/home/claude/studio/toolkit/blender'); import cine
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cine.set_cinematic_defaults(sc, samples=24, res=(540, 960))
cine.sky_sun()
bpy.ops.mesh.primitive_plane_add(size=20); p = bpy.context.object
cine.ocean_like_water(p)
bpy.ops.mesh.primitive_cube_add(location=(0, 2, 0.8), scale=(1.5, 1.5, 0.8))
cam = cine.add_camera('cam', lens=35, fstop=5, focus=8)
cam.location = (0, -10, 3); cine.aim(cam, (0, 2, 0.5))
sc.render.filepath = '/home/claude/studio/toolkit/blender/test.png'
bpy.ops.render.render(write_still=True); print('ok')
