# Photoreal Cycles render of a three.js kitchen scene exported to GLB (kitchen2-scene.html?export=1).
# Usage: python3.11 renders/blender_render.py scene.glb out.png [width] [samples]   (needs `pip install bpy==4.2.0`)
# three.js (x, y, z) maps to Blender (x, -z, y): the kitchen wall is at Blender y = 0, the room extends to -y.
import sys, math, time
import bpy
from mathutils import Vector

glb, out = sys.argv[1], sys.argv[2]
W = int(sys.argv[3]) if len(sys.argv) > 3 else 2400
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 256

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o)
sc.camera = next(o for o in sc.objects if o.type == 'CAMERA')
sc.camera.data.sensor_fit = 'VERTICAL'; sc.camera.data.angle_y = math.radians(float(__import__('os').environ.get('FOV', '46')))

def P(x, y, z):  # three.js -> Blender
    return Vector((x, -z, y))

# ---------- material polish ----------
def bsdf(mat):
    return next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if mat and mat.use_nodes else None
for mat in bpy.data.materials:
    b = bsdf(mat)
    if not b:
        continue
    n = mat.name.split('.')[0]
    if n == 'cash':        # supermatte cashmere fronts
        b.inputs['Roughness'].default_value = 0.55
        b.inputs['Base Color'].default_value = (0.56, 0.5, 0.43, 1)
        b.inputs['Sheen Weight'].default_value = 0.15
    elif n == 'quartz':
        b.inputs['Roughness'].default_value = 0.1
        b.inputs['Coat Weight'].default_value = 0.4
        b.inputs['Coat Roughness'].default_value = 0.05
    elif n == 'oak':
        b.inputs['Roughness'].default_value = 0.5
    elif n == 'floor':
        b.inputs['Roughness'].default_value = 0.38
    elif n in ('wall', 'ceiling'):
        b.inputs['Roughness'].default_value = 0.9
    elif n == 'led':
        b.inputs['Emission Strength'].default_value = 25
    elif n in ('display', 'displayW'):
        b.inputs['Emission Strength'].default_value = 6
    elif n == 'blackGlass':
        b.inputs['Roughness'].default_value = 0.03
        b.inputs['Coat Weight'].default_value = 1.0
    elif n == 'hob':             # satin black glass: no mirror-white glare from the backsplash
        b.inputs['Roughness'].default_value = 0.18
        b.inputs['Specular IOR Level'].default_value = 0.3

# ---------- lights ----------
def light(kind, name, loc, power, rot=(0, 0, 0), **kw):
    d = bpy.data.lights.new(name, kind); d.energy = power
    for k, v in kw.items():
        setattr(d, k, v)
    o = bpy.data.objects.new(name, d); o.location = loc; o.rotation_euler = rot
    sc.collection.objects.link(o); return o

CEIL = 2.77
for i, (x, z) in enumerate([(0.7, 0.95), (2.0, 0.95), (3.4, 1.1), (1.0, 3.6), (3.2, 3.6)]):
    light('SPOT', f'down{i}', P(x, CEIL - 0.03, z), 45, spot_size=math.radians(100), spot_blend=0.9,
          shadow_soft_size=0.04, color=(1.0, 0.92, 0.82))
for i, x in enumerate([1.25, 2.085, 2.92]):       # three black tube pendants
    light('SPOT', f'pend{i}', P(x, 1.935, 2.125), 22, spot_size=math.radians(55), spot_blend=0.7,
          shadow_soft_size=0.025, color=(1.0, 0.88, 0.74))
for i in range(8):                                 # LED strip under the uppers
    light('AREA', f'led{i}', P(0.35 + i * 0.52, 1.49, 0.06), 6, shape='RECTANGLE', size=0.5, size_y=0.02,
          color=(1.0, 0.9, 0.78))
# large soft fill from the open room side (behind the camera), like a big window
light('AREA', 'window', P(2.1, 1.5, 8.5), 500, rot=(math.radians(90), 0, 0), shape='RECTANGLE', size=4.5, size_y=2.4,
      color=(1.0, 0.98, 0.95))
# low afternoon sun through that side
light('SUN', 'sun', (0, 0, 0), 2.2, rot=(math.radians(68), 0, math.radians(200)), angle=math.radians(1.5),
      color=(1.0, 0.93, 0.84))

world = bpy.data.worlds.new('World'); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.86, 0.9, 0.96, 1); bg.inputs[1].default_value = 0.3

# ---------- render ----------
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.device = 'CPU'; cy.samples = SAMPLES; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 8; cy.diffuse_bounces = 4; cy.glossy_bounces = 4; cy.transmission_bounces = 8
cy.caustics_reflective = False; cy.caustics_refractive = False; cy.blur_glossy = 1.0
sc.render.resolution_x = W; sc.render.resolution_y = W * 2 // 3; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = float(__import__('os').environ.get('EXPOSURE', '-0.8'))
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out
t = time.time(); bpy.ops.render.render(write_still=True); print('rendered', out, f'{time.time() - t:.0f}s')
