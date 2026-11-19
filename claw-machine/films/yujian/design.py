"""Design stills. blender -b --factory-startup -P films/yujian/design.py -- --what dog --out films/yujian/docs/dog.png [--samples 96] [--scale 50]"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from yj.common import *
from yj import mats as M, plush as PL

scene = init_scene(samples=int(arg("--samples", "96")), scale=int(arg("--scale", "50")))
what = arg("--what", "dog").split(",")
stage = coll("stage")
# turntable ground: felt
ground = box("ground", (2, 2, 0.02), stage, (0, 0, -0.01), M.fabric("ground", "#D9C4A0", "cotton_jersey", scale=5, bump=0.8))
built = []
for i, w in enumerate(what):
    P = getattr(PL, "build_" + w)(stage)
    P.root.location.x = (i - (len(what) - 1) / 2) * 0.13
    P.root.rotation_euler.z = math.radians(float(arg("--yaw", "-20")))
    built.append(P)
def area(name, loc, target, size, energy, col):
    L = bpy.data.lights.new(name, "AREA"); L.size = size; L.energy = energy; L.color = col
    o = new_obj(name, L, stage); look_at(o, loc, target); return o
area("key", (-0.35, -0.45, 0.5), (0, 0, 0.06), 0.35, 7, (1.0, 0.86, 0.68))
area("fill", (0.5, -0.3, 0.2), (0, 0, 0.06), 0.5, 1.5, (0.6, 0.75, 1.0))
area("rim", (0.2, 0.5, 0.35), (0, 0, 0.08), 0.3, 5, (1.0, 0.9, 0.8))
w = bpy.data.worlds.new("w"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.045, 0.06, 1)
cam = new_obj("cam", bpy.data.cameras.new("cam"), stage)
cam.data.lens = float(arg("--lens", "85"))
dist = float(arg("--dist", "0.9")) + 0.1 * (len(what) - 1)
look_at(cam, (0.0, -dist, 0.16), (0, 0, 0.062))
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = dist - 0.03; cam.data.dof.aperture_fstop = 4.0
cam.data.clip_start = 0.01
scene.camera = cam
scene.view_settings.view_transform = arg("--view", "Standard")
tryset(scene.view_settings, "look", arg("--look", "None"))
out = os.path.abspath(arg("--out", "films/yujian/docs/design.png"))
scene.render.filepath = out
t0 = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER_SECONDS %.1f" % (time.time() - t0), out)
