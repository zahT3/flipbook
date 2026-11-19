"""《遇见》: the claw machine film. Builds the whole scene, poses it for a time, renders.

  blender -b --factory-startup -P films/yujian/film.py -- --frames 0-701 --out out/yujian/frames [--scale 50] [--samples 64] [--furq 0.5]
  ... --times 12.8,15.0 --out out/yujian/check        (stills at clip times, named t<seconds>.png)
  ... --cam wide_out --times 0                        (force one camera: design stills)
Frame numbers count twelfths of a second (the film is shot on twos): frame f is clip time f / 12.
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from yj.common import *
from yj import mats as M, plush as PL, claw as CL, machine as MC, anim as AN

SPF = 12
scene = init_scene(samples=int(arg("--samples", "64")), scale=int(arg("--scale", "100")))
scene.view_settings.view_transform = arg("--view", "Standard")
if arg("--look"): scene.view_settings.look = arg("--look")
scene.view_settings.exposure = float(arg("--exposure", "0"))
world = AN.build_all(scene)

OUT = os.path.abspath(arg("--out", "out/yujian/frames"))
os.makedirs(OUT, exist_ok=True)
jobs = []
if arg("--times"):
    for s in arg("--times").split(","):
        jobs.append((float(s), os.path.join(OUT, "t%06.2f.png" % float(s))))
else:
    for f in parse_frames(arg("--frames", "0")):
        jobs.append((f / SPF, os.path.join(OUT, "%04d.png" % f)))
if flag("--reverse"): jobs.reverse()          # lets a second machine work back from the end of a range
if flag("--save"):
    AN.pose(world, jobs[0][0], arg("--cam"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg("--save")))
t_all = time.time()
for t, fp in jobs:
    if os.path.exists(fp) and not flag("--force"): continue
    AN.pose(world, t, arg("--cam"))
    scene.render.filepath = fp
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("FRAME t=%.3f %.1fs %s" % (t, time.time() - t0, fp), flush=True)
print("TOTAL_SECONDS %.1f" % (time.time() - t_all), flush=True)
