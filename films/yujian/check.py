"""Geometry checker: pose every drawing (no rendering) and report things that pass through each other.
  blender -b --factory-startup -P films/yujian/check.py -- --furq 0.02 [--frames 0-701]
Reports, per shot: claw parts outside the cabinet or under the bed; plushes outside / under the bed;
plushes inside each other while one of them moves; fingers inside a plush they are not holding; the mitten through the glass;
a plush through the prize door's flap, frame, shaft walls or bin floor."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from yj.common import *
from yj import claw as CL, anim as AN, machine as MC

scene = init_scene(samples=1, scale=10)
W = AN.build_all(scene)
SPH = {"dog": [((0, 0, 0.040), 0.036), ((0, -0.003, 0.092), 0.037)],
       "clawd": [((-0.022, 0, 0.055), 0.028), ((0.022, 0, 0.055), 0.028)],
       "frog": [((0, 0, 0.034), 0.036)], "star": [((0, 0, 0.052), 0.026)], "octo": [((0, 0, 0.050), 0.038)],
       "mush": [((0, 0, 0.030), 0.023), ((0, 0, 0.070), 0.036)], "cloud": [((0, 0, 0.040), 0.032), ((-0.030, 0, 0.034), 0.024), ((0.033, 0, 0.032), 0.022)]}
def kind(n): return n.rstrip("2")
FING = [Vector((x * CL.S, 0, z * CL.S)) for x, z in CL.FINGER]
def in_hole(p, m=0.0): return HOLE[0] - m < p.x < HOLE[1] + m and HOLE[2] - m < p.y < HOLE[3] + m
issues = {}
def note(shot, key, t, amount):
    k = (shot, key)
    a = issues.setdefault(k, [t, t, 0.0])
    a[1] = t; a[2] = max(a[2], amount)
frames = parse_frames(arg("--frames", "0-701"))
prev = {}
for f in frames:
    t = f / 12
    shot = AN.pose(W, t)
    bpy.context.view_layer.update()
    vis = {n: P for n, P in W.plush.items() if not P.c.hide_render}
    sph = {}
    for n, P in vis.items():
        m = P.root.matrix_world
        sph[n] = [(m @ Vector(c), r) for c, r in SPH[kind(n)]]
    moving = {n: (n in prev and (prev[n] - P.root.matrix_world.translation).length > 0.0008) for n, P in vis.items()}
    hub = W.claw.hub.matrix_world.translation.copy()
    inside = Y0 - 0.002 < hub.y                     # the claw is always inside; plushes may be outside (exit door)
    # --- claw against the cabinet
    pts = [("hub", hub, 0.022)]
    for i, piv in enumerate(W.claw.fingers):
        m = piv.matrix_world
        for j, p in enumerate(FING[2:]): pts.append(("finger%d" % i, m @ p, 0.006))
    for name, p, r in pts:
        for lab, d in (("x<left glass", X0 + r - p.x), ("x>right glass", p.x + r - X1), ("y<front glass", Y0 + r - p.y), ("y>back wall", p.y + r - Y1)):
            if d > 0.002: note(shot, "%s %s" % (name, lab), t, d)
        if p.z - r < -0.004 and not in_hole(p): note(shot, "%s under the bed" % name, t, -(p.z - r))
        if name.startswith("finger") and in_hole(p, 0.004) is False and HOLE[0] - 0.004 < p.x < HOLE[1] + 0.012 and HOLE[2] < p.y < HOLE[3] + 0.012 and p.z < 0.062:
            note(shot, "%s through the chute guard" % name, t, 0.062 - p.z)
    # --- plushes against the cabinet (only while they are inside it and below the ceiling)
    for n, ss_ in sph.items():
        for c, r in ss_:
            if c.y < Y0 - 0.03 or c.z > ZT - 0.03 or c.z < -0.03: continue
            for lab, d in (("x<left glass", X0 + r - c.x), ("x>right glass", c.x + r - X1), ("y<front glass", Y0 + r - c.y), ("y>back wall", c.y + r - Y1)):
                if d > 0.008: note(shot, "%s %s" % (n, lab), t, d)
            if c.z - r < -0.016 and not in_hole(c, -0.02): note(shot, "%s under the bed" % n, t, -(c.z - r))
    # --- plush against plush
    names = sorted(sph)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if not (moving[a] or moving[b]) or shot == "s12": continue
            dmax = max(ra + rb - (ca - cb).length for ca, ra in sph[a] for cb, rb in sph[b])
            if dmax > 0.012: note(shot, "%s inside %s" % (a, b), t, dmax)
    # --- plushes at the prize door: the flap, the door frame, the shaft walls and the bin floor (real vertices, not spheres)
    Mx = W.machine
    fl = Mx.flap_obj; finv = fl.matrix_world.inverted(); fhx = (Mx.door_w - 0.004) / 2
    dz0, dz1 = Mx.door_c.z - Mx.door_h / 2, Mx.door_c.z + Mx.door_h / 2
    for n, P in vis.items():
        if P.root.matrix_world.translation.z > -0.2: continue
        lo = hi = 0.0; near = 9.0; jamb = lintel = sill = wall = floor = 0.0
        for o in P.c.all_objects:
            if o.type != "MESH": continue
            mw = o.matrix_world
            for v in o.data.vertices:
                p = mw @ v.co
                q = finv @ p
                if abs(q.x) <= fhx and 0 <= q.z <= Mx.flap_len: lo = min(lo, q.y); hi = max(hi, q.y); near = min(near, abs(q.y))
                dx = abs(p.x - Mx.door_c.x)
                if Y0 - 0.036 <= p.y <= Y0 and dz0 - 0.03 < p.z < dz1 + 0.05:        # passing through the front panel
                    jamb = max(jamb, dx - Mx.door_w / 2); lintel = max(lintel, p.z - dz1); sill = max(sill, dz0 - p.z)
                if p.y > Y0 and p.z < dz1 + 0.05:                                     # inside the shaft
                    wall = max(wall, dx - (HOLE[1] - HOLE[0]) / 2, p.y - HOLE[3]); floor = max(floor, Mx.bin_floor_z - p.z)
        thru = min(hi, -lo) - 0.0015
        if flag("--gap"): print("GAP f%d %s: nearest vertex to the flap %.1f mm, flap %.1f deg" % (f, n, (near - 0.0015) * 1000, math.degrees(Mx.flap.rotation_euler.x)))
        if thru > 0.002: note(shot, "%s through the door flap" % n, t, thru)
        for lab, d in (("jamb", jamb), ("lintel", lintel), ("sill", sill)):
            if d > 0.003: note(shot, "%s through the door %s" % (n, lab), t, d)
        if wall > 0.003: note(shot, "%s through the shaft wall" % n, t, wall)
        if floor > 0.004: note(shot, "%s under the bin floor" % n, t, floor)
    # --- fingers against plushes they are not holding
    for n, ss_ in sph.items():
        c0 = ss_[0][0]
        held = math.hypot(c0.x - hub.x, c0.y - hub.y) < 0.05 and c0.z < hub.z
        if held: continue
        for name, p, r in pts[1:]:
            d = max(rr - (p - c).length for c, rr in ss_)
            if d > 0.010: note(shot, "%s inside %s" % (name, n), t, d)
    # --- the mitten against the glass and the cabinet front
    if not W.person.c.hide_render:
        hm = W.person.hand.matrix_world
        if hm.translation.y < 0 and abs(hm.translation.x) < 1:
            for loc in ((0, 0.016, 0.006), (0, 0.012, 0.045), (0, 0.012, -0.03), (-0.034, 0.010, -0.012), (0, 0, 0.052), (0, 0, -0.07)):
                p = hm @ Vector(loc)
                lim = Y0 - 0.001 if p.z > -0.02 else Y0 - 0.031
                if p.y > lim and X0 - 0.03 < p.x < X1 + 0.03 and p.z > -0.5: note(shot, "mitten through the %s" % ("glass" if p.z > -0.02 else "cabinet front"), t, p.y - lim)
                q = W.machine.flap_obj.matrix_world.inverted() @ p
                if abs(q.x) < W.machine.door_w / 2 and -0.004 < q.z < W.machine.flap_len + 0.004 and abs(q.y) < 0.0055: note(shot, "mitten through the door flap", t, 0.0055 - abs(q.y))
    prev = {n: P.root.matrix_world.translation.copy() for n, P in vis.items()}
print("CHECK_BEGIN")
for (shot, key), (t0, t1, amt) in sorted(issues.items(), key=lambda kv: kv[1][0]):
    print("%-5s %-34s %6.2f-%6.2f  up to %4.1f cm" % (shot, key, t0, t1, amt * 100))
print("CHECK_END %d issues" % len(issues))
