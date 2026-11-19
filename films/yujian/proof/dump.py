"""Data for the proof film, no rendering:
  blender -b --factory-startup -P films/yujian/proof/dump.py -- --out out/yujian/proof/data.json
 - the claw's animation channels for all 702 drawings, straight from yj/anim.py's pose(t)
 - the fur strand count of every plush (parent strands x rendered children), at render quality
 - the dog's objects, so build.py can show it being assembled part by part"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bpy
from yj.common import *
from yj import anim as AN

scene = init_scene(samples=1, scale=10)
W = AN.build_all(scene)
out = {"fur": {}, "dog_objects": [], "frames": []}
for name, P in W.plush.items():
    n = 0
    for o in P.c.all_objects:
        for m in o.modifiers:
            if m.type == "PARTICLE_SYSTEM":
                s = m.particle_system.settings
                n += s.count * (s.rendered_child_count if s.child_type != "NONE" else 1)
    out["fur"][name] = n
out["dog_objects"] = sorted(o.name for o in W.plush["dog"].c.all_objects if o.type in ("MESH", "CURVE"))
for f in range(702):
    shot = AN.pose(W, f / 12)
    st = W.claw.state
    op = st["open"] if isinstance(st["open"], (list, tuple)) else [st["open"]] * 3
    out["frames"].append(dict(f=f, shot=shot, x=st["x"], y=st["y"], z=st["z"], open=[float(a) for a in op], slack=float(st["slack"])))
p = os.path.abspath(arg("--out", "out/yujian/proof/data.json"))
json.dump(out, open(p, "w"))
print("DUMP_DONE", p, sum(out["fur"].values()), len(out["frames"]))
