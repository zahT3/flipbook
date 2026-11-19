"""Build the world and pose it for any clip time. Everything is a pure function of t."""
import bpy, math
from mathutils import Vector, Euler, Quaternion
from .common import *
from . import mats as M, plush as PL, claw as CL, machine as MC

class World: pass
F = 1 / 12.0                      # one drawing (the film is shot on twos)
def fr(n): return n / 12.0

# name, kind, builder kwargs, rest (x, y, yaw deg, lean deg)
CAST = [
    ("dog",    "dog",   {},                                         (0.070, -0.090,   0,  0)),
    ("clawd",  "clawd", {},                                         (-0.050, -0.105, 8,  0)),
    ("frog",   "frog",  {},                                         (0.165, -0.125, -14,  0)),
    ("star",   "star",  {},                                         (-0.170, 0.030,  12, -16)),
    ("octo",   "octo",  {},                                         (-0.055, 0.035,   6,  0)),
    ("mush",   "mush",  {},                                         (0.175, 0.050,  -10,  4)),
    ("cloud",  "cloud", {},                                         (0.085, 0.100,   -4,  0)),
    ("frog2",  "frog",  dict(col="#E3B8A0", belly="#F6EEDC"),       (-0.180, 0.130,  20,  0)),
    ("star2",  "star",  dict(col="#D99A9A", patch_col="#8FB3A8"),   (0.000, 0.150,   -6, -20)),
    ("octo2",  "octo",  dict(col="#E79A7C"),                        (0.185, 0.135,  -18,  0)),
    ("mush2",  "mush",  dict(cap="#D9A441", dots="#FFF6E0"),        (-0.085, 0.125,   8, -5)),
    ("cloud2", "cloud", dict(col="#EFE6D4"),                        (-0.030, -0.002, 12,  0)),
    ("clawd2", "clawd", {},                                         (0.02, -0.03, -6, 0)),
]
REST = {n: r for n, _, _, r in CAST}
ALL = [n for n, _, _, _ in CAST if n != "clawd2"]
D0 = (0.070, -0.090)              # the dog's first seat
D1 = (0.115, -0.150)              # by the glass, next to the hand print
CH = (-0.150, -0.100)            # where things are let go: over the hole, as far from the two glass walls as it allows
CH_SPIN = 0                      # no turn on the way: a turned claw put a finger across the face of whatever it carried
Z_CARRY = 0.27                   # hub height while carrying: clears every plush still sitting on the bed
Z_HI = 0.305                      # claw parked height (hub hinge level)
HAND_ON = Vector((MC.HAND_POS.x, Y0 - 0.027, MC.HAND_POS.z))
WIDE = ((0.012, -1.50, 0.215), (0.0, 0.0, 0.168), 64, 3.2, (0.05, -0.08, 0.08))

SHOTS = [(0, "s1"), (40, "s2"), (90, "s3a"), (123, "s3b"), (138, "s3c"), (154, "s4"), (215, "s5a"), (235, "s5b"), (256, "s5c"), (280, "s6"),
         (341, "s7a"), (372, "s7b"), (405, "s8a"), (431, "s8b"), (451, "s8c"), (467, "s9a"), (487, "s9b"), (532, "s10a"),
         (568, "s10b"), (593, "s10c"), (619, "s11"), (655, "s12")]
END = 702
def shot_at(t):
    f = t * 12 + 1e-6
    cur = SHOTS[0]
    for i, s in enumerate(SHOTS):
        if f >= s[0]: cur = s; nxt = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END
    return cur[1], cur[0] / 12.0, nxt / 12.0

def build_all(scene):
    W = World()
    root = coll("film")
    W.machine = MC.build_machine(root)
    W.shop = MC.build_shop(root)
    W.person = MC.build_person(root)
    W.claw = CL.Claw(root)
    W.plush = {}
    for name, kind, kw, start in CAST:
        P = PL.KINDS[kind](root, name=name, **kw) if kind != "dog" else PL.build_dog(root)
        W.plush[name] = P
    dog = W.plush["dog"]
    dog.ear_rest = {k: dog.p[k].rotation_euler.copy() for k in ("earL", "earR")}
    dog.tail_rest = dog.p["tail"].rotation_euler.copy()
    # the coin
    W.coin = cyl("coin", 0.0115, 0.0115, 0.0018, root, m=M.worn_metal("coin_brass", col="#C9A24A", oil=0.4, scale=40), seg_n=32)
    W.cam = new_obj("cam", bpy.data.cameras.new("cam"), root)
    W.cam.data.dof.use_dof = True
    W.cam.data.clip_start = 0.02; W.cam.data.clip_end = 30
    W.cam.data.sensor_width = 36
    scene.camera = W.cam
    W.scene = scene
    W.fill_base = W.machine.fill.energy * 0.8; W.key_base = W.machine.key.energy * 0.68; W.front_base = W.machine.front_row.energy * 0.7; W.back_base = W.machine.back_row.energy * 0.7
    return W

def set_cam(W, pos, target, lens, fstop, focus=None, roll=0.0):
    look_at(W.cam, pos, target, roll)
    W.cam.data.lens = lens
    W.cam.data.dof.aperture_fstop = fstop
    f = Vector(focus if focus is not None else target)
    d = (f - Vector(pos)).dot((Vector(target) - Vector(pos)).normalized())
    W.cam.data.dof.focus_distance = max(0.05, d)

def lights(W, key=1.0, bulbs=1.0, last=0.0, shop=1.0, morning=0.0):
    """bulbs: one level or 18 (front row 0-8 left to right, back row 9-17)."""
    Mx = W.machine
    if isinstance(bulbs, (int, float)): bulbs = [bulbs] * 18
    for m, b in zip(Mx.bulbs, bulbs): M.set_emit(m, 2.1 * b)
    Mx.key.energy = W.key_base * key
    Mx.fill.energy = W.fill_base * key
    Mx.front_row.energy = W.front_base * sum(bulbs[:9]) / 9
    Mx.back_row.energy = W.back_base * sum(bulbs[9:]) / 9
    Mx.last_lamp.energy = 4.5 * last
    if last > 0.5 and sum(bulbs) == 0: M.set_emit(Mx.bulbs[3], 2.4 * last)      # the one bulb that stays on
    MC.set_shop(W.shop, shop, morning)

def spill(W, target, energy):
    """Warm light from inside the cabinet onto something just outside the front glass."""
    t = Vector(target)
    look_at(W.machine.spill_o, (t.x + 0.03, -0.05, 0.43), t)
    W.machine.spill.energy = energy

def place(P, x, y, z=0.0, yaw=0.0, lean=0.0, roll=0.0, sq=0.0):
    """Seat a plush. sq > 0 squashes (wider, shorter), < 0 stretches. lean: + onto its face, - onto its back."""
    P.root.rotation_mode = "YXZ"
    P.root.location = (x, y, z - 0.006)
    P.root.rotation_euler = Euler((math.radians(lean), math.radians(roll), math.radians(yaw)), "YXZ")
    P.sq.scale = (1 + sq * 0.5, 1 + sq * 0.5, 1 - sq)

def grip(P, tight=1.0):
    """(height of the hub above the plush's seat while it is held, finger angle)."""
    return P.h + 0.034, CL.angle_for_radius(max(0.010, P.rad * 0.80 * tight))

def hang(W, P, yaw=0.0, lean=0.0, sq=-0.04, tight=1.0, dz=0.0):
    """Put a plush in the claw's grip (call after claw.pose)."""
    h, _ = grip(P, tight)
    hub = W.claw.hub
    q = hub.rotation_quaternion @ Euler((math.radians(lean), 0, math.radians(yaw)), "YXZ").to_quaternion()
    P.root.rotation_mode = "QUATERNION"
    P.root.rotation_quaternion = q
    P.root.location = hub.location + hub.rotation_quaternion @ Vector((0, 0, -h + dz))
    P.sq.scale = (1 + sq * 0.5, 1 + sq * 0.5, 1 - sq)

def dog_act(W, head_yaw=0.0, head_pitch=0.0, head_roll=0.0, perk=0.0, ear_swing=0.0, ear_flap=0.0, tail=0.0):
    """head_yaw + = toward its left (screen right when it faces the camera); head_pitch + = up.
    perk 0..1 lifts both ears; ear_swing (deg) drags them front/back; ear_flap flares them sideways."""
    d = W.plush["dog"]
    d.p["neck"].rotation_euler = Euler((math.radians(-head_pitch), math.radians(head_roll), math.radians(head_yaw)), "YXZ")
    for k, sx, lag in (("earL", -1, 1.25), ("earR", 1, 1.0)):
        r = d.ear_rest[k]
        d.p[k].rotation_euler = Euler((r.x + math.radians(ear_swing * lag), r.y - sx * math.radians(perk * 62 + ear_flap * lag), r.z))
    d.p["tail"].rotation_euler = Euler((d.tail_rest.x, 0, math.radians(tail)))

def fall(t, t0, z0, g=3.2):
    """Height of something let go at t0 (slow gravity: a stop-motion drop)."""
    return z0 - 0.5 * g * max(0.0, t - t0) ** 2

def claw_keys(t, keys):
    """keys: [(time, dict)] -> interpolated dict (smoothstep). Missing channels carry forward."""
    chans = {}
    cur = {}
    for tm, d in keys:
        cur = {**cur, **d}
        for k, v in cur.items(): chans.setdefault(k, []).append((tm, v))
    return {k: kf(t, v) for k, v in chans.items()}

def present(W, names):
    for n, P in W.plush.items():
        P.hide(n not in names)
        if n in names:
            x, y, yaw, lean = REST[n]
            place(P, x, y, 0, yaw, lean)

def jitter(W, t, amt=1.0):
    """The animator's hand: the claw never comes back to exactly the same place."""
    f = int(round(t * 12))
    return ((hsh("jx", f) - 0.5) * 0.5 * amt, (hsh("jy", f) - 0.5) * 0.5 * amt)

# ================================================================ shots
def s1(W, t, lt, dur):
    present(W, ALL)
    dog = W.plush["dog"]
    h, ga = grip(dog, 1.05)
    k = claw_keys(t, [(0.0, dict(z=0.300, open=52)), (1.25, dict(z=h + 0.004)), (1.33, dict(open=52)), (1.58, dict(open=30)), (1.75, dict(open=30)),
                      (2.0, dict(open=ga, z=h + 0.004)), (2.17, dict(z=h + 0.002)), (3.4, dict(z=h + 0.085))])
    jx, jy = jitter(W, t)
    sw = 1.5 * spring(t, 2.17, 1.4, 1.2)
    W.claw.pose(D0[0], D0[1], k["z"], open=k["open"], swing=(jx + sw, jy))
    if t >= 2.17:
        hang(W, dog, yaw=4 * seg(t, 2.17, 3.4), lean=3 * spring(t, 2.17, 1.6, 1.5), tight=1.05)
        dog_act(W, ear_swing=-14 * seg(t, 2.17, 2.5) + 6 * spring(t, 2.5, 1.5, 2.0), ear_flap=8 * seg(t, 2.17, 2.6))
        c2 = W.plush["cloud2"]; x, y, yaw, lean = REST["cloud2"]
        place(c2, x, y, 0, yaw + 6 * spring(t, 2.25, 2.0, 3.0), lean + 5 * spring(t, 2.25, 2.0, 3.0))
    else:
        place(dog, D0[0], D0[1], 0, 0, 0, sq=0.05 * seg(t, 1.75, 2.0))
        dog_act(W, ear_flap=6 * seg(t, 1.6, 2.0))
    hand_on_glass(W, 0.0)
    lights(W)
    p = ss(seg(t, 0, 3.4))
    set_cam(W, (0.012 + 0.01 * p, -1.50 + 0.10 * p, 0.215), (0.0 + 0.012 * p, 0.0, 0.168 - 0.004 * p), 64, 4.0, (0.05, -0.08, 0.10))

def s2(W, t, lt, dur):
    present(W, ALL)
    dog = W.plush["dog"]
    h, ga = grip(dog, 1.05)
    top = h + 0.135
    k = claw_keys(t, [(3.33, dict(z=h + 0.080)), (4.58, dict(z=top)), (4.75, dict(z=top - 0.004)), (5.75, dict(z=h + 0.004)), (6.3, dict(z=h + 0.004)), (7.5, dict(z=h + 0.12))], )
    z = kf(t, [(3.33, h + 0.080), (4.58, top)], eo) if t < 4.58 else k["z"]
    # tremble while it holds on; the fingers let go one at a time
    tr = 2.2 * (1 if int(t * 12) % 2 else -1) * seg(t, 3.6, 4.2) * (1 - seg(t, 4.9, 5.2))
    o = [ga + tr, ga - tr * 0.6, ga + tr * 0.4]
    for i, t0 in enumerate((5.17, 5.5, 5.83)):
        o[i] = lerp(o[i], 40, ss(seg(t, t0, t0 + 0.25)))
    o[2] = kf(t, [(5.83, ga), (6.08, ga + 12), (6.33, ga + 12), (6.6, 44)]) if t >= 5.83 else o[2]   # the last finger lingers on its head
    if t > 6.6: o = [lerp(40, 30, seg(t, 6.6, 7.4))] * 2 + [lerp(44, 30, seg(t, 6.6, 7.4))]
    tilt_x = kf(t, [(4.5, 0), (4.75, -7), (4.95, -7), (5.2, 7), (5.4, 7), (5.6, 0)])                # looks left, looks right
    jx, jy = jitter(W, t)
    W.claw.pose(D0[0], D0[1], z, open=o, swing=(jx, jy), tilt=(tilt_x, 0), spin=20 * seg(t, 3.33, 5.0))
    if t < 5.83:
        hang(W, dog, yaw=4 + 20 * seg(t, 3.33, 5.0) - 24 * ss(seg(t, 5.0, 5.75)), lean=0, tight=1.05,
             sq=-0.04 + 0.04 * seg(t, 5.2, 5.8))
        dog_act(W, ear_swing=-10 * (1 - eo(seg(t, 3.33, 4.6))) + 12 * seg(t, 4.75, 5.3) * (1 - seg(t, 5.6, 5.83)), ear_flap=8)
    else:
        place(dog, D0[0], D0[1], 0, 0, 0, sq=0.06 * spring(t, 5.83, 2.2, 5.0))
        dog_act(W, ear_swing=10 * spring(t, 5.83, 1.8, 2.2), ear_flap=8 * spring(t, 5.83, 1.5, 2.0), head_pitch=6 * ss(seg(t, 6.6, 7.2)))
    # the player outside: the mitten slides down the glass and goes
    hand_on_glass(W, ss(seg(t, 6.5, 7.33)))
    lights(W, bulbs=1.0 - 0.06 * (1 if int(t * 12) % 3 == 0 else 0) * seg(t, 3.8, 4.4) * (1 - seg(t, 5.0, 5.3)))
    cz = 0.225 + 0.02 * ss(seg(t, 3.33, 4.6)) - 0.075 * ss(seg(t, 4.75, 5.8))
    set_cam(W, (-0.10, -1.22, 0.23), (0.085, -0.09, cz), 66, 4.0, (D0[0], D0[1] - 0.02, 0.2))

def hand_on_glass(W, off):
    """The mitten pressed on the glass from outside, the arm coming up from below; off 0..1 slides it down and takes it away."""
    W.person.c.hide_render = False
    W.person.root.location = (3, -3, -2)
    a, b = ss(min(1.0, off * 2)), ss(max(0.0, off * 2 - 1))
    W.person.hand.location = HAND_ON + Vector((0, -0.003 * a, -0.050 * a)) + Vector((0.03 * b, -0.24 * b, -0.20 * b * b))
    W.person.hand.rotation_euler = Euler((math.radians(-8 - 14 * b), math.radians(-14 + 8 * a), 0))
    W.person.wrist.rotation_euler = Euler((math.radians(-42 + 10 * b), 0, 0))

def deliver(W, t, P, src, t_down, t_close, t_lift, t_go, t_at, t_rel, z_carry=Z_CARRY, start_z=Z_HI):
    """A no-nonsense delivery: down, shut, up, across, open. Returns after posing claw and plush."""
    h, ga = grip(P)
    p = ss(seg(t, t_go, t_at))
    x = lerp(src[0], CH[0], p); y = lerp(src[1], CH[1], p)
    z = kf(t, [(t_down, start_z), (t_close - 0.08, h + 0.003), (t_close + 0.12, h + 0.003), (t_lift, z_carry)])
    o = kf(t, [(t_close - 0.02, 55), (t_close + 0.1, ga), (t_rel, ga), (t_rel + 0.1, 62)], ease=eo)
    # the carriage starts and stops; the claw swings a little behind it
    sw = -5 * math.sin(math.pi * seg(t, t_go, t_go + 0.5)) * (1 if t < t_go + 0.5 else 0) + 4 * spring(t, t_at, 1.6, 3.0) * (1 if t >= t_at else 0)
    jx, jy = jitter(W, t, 0.6)
    W.claw.pose(x, y, z, open=o, swing=(sw + jx, jy), spin=CH_SPIN * p)
    if t < t_close + 0.05:
        px, py, yaw, lean = REST[P.name]
        place(P, src[0], src[1], 0, yaw, lean, sq=0.08 * seg(t, t_close - 0.05, t_close + 0.05))
    elif t < t_rel + 0.04:
        hang(W, P, yaw=REST[P.name][2] - CH_SPIN * p, lean=2 * spring(t, t_close + 0.1, 1.5, 2.0))
    else:
        drop_into_chute(P, t, t_rel + 0.04, z_carry - grip(P)[0], REST[P.name][2])

def drop_into_chute(P, t, t0, z0, yaw):
    zf = fall(t, t0, z0)
    place(P, CH[0], CH[1], zf, yaw + 60 * (t - t0), 100 * (t - t0))
    if zf < -0.16: P.hide(True)

def pass_to_chute(W, t, P, t_in, t_at, t_rel, t_out):
    """Seen from the chute: the claw comes in from the right already holding something, lets it go, and leaves for the next."""
    h, ga = grip(P)
    p_in = ss(seg(t, t_in, t_at)); p_out = ss(seg(t, t_out, t_out + 0.7))
    x = lerp(0.13, CH[0], p_in) + 0.24 * p_out; y = lerp(-0.11, CH[1], p_in)
    o = kf(t, [(t_rel, ga), (t_rel + 0.1, 62), (t_out, 62), (t_out + 0.3, 20)], ease=eo)
    sw = 4 * spring(t, t_at, 1.6, 3.0) * (t >= t_at) + 5 * math.sin(math.pi * seg(t, t_out, t_out + 0.5)) * (t_out <= t < t_out + 0.5)
    jx, jy = jitter(W, t, 0.6)
    W.claw.pose(x, y, Z_CARRY, open=o, swing=(sw + jx, jy), spin=CH_SPIN * (p_in - p_out))
    if t < t_rel + 0.04: hang(W, P, yaw=8, lean=3 * spring(t, t_at, 1.5, 2.0) * (t >= t_at))
    else: drop_into_chute(P, t, t_rel + 0.04, Z_CARRY - h, 8)

def s3a(W, t, lt, dur):
    present(W, ALL)
    P = W.plush["clawd"]
    deliver(W, t, P, REST["clawd"][:2], 7.42, 8.0, 8.75, 8.83, 9.67, 9.83)
    dog_act(W, head_yaw=-14 * ss(seg(t, 9.0, 9.6)))                     # the dog watches it go
    lights(W)
    p = ss(seg(t, 8.8, 9.7))
    up = ss(seg(t, 8.1, 8.8))
    set_cam(W, (-0.10, -1.18, 0.21), (-0.070 - 0.035 * p, -0.08, 0.125 + 0.090 * up), 82, 4.0, (-0.05 - 0.10 * p, -0.11, 0.14))

CHUTE_CAM = ((-0.13, -1.12, 0.215), (-0.105, -0.10, 0.205), 74, 4.0, (CH[0], CH[1], 0.17))
def s3b(W, t, lt, dur):
    present(W, [n for n in ALL if n != "clawd"])
    pass_to_chute(W, t, W.plush["frog"], 10.17, 10.67, 10.83, 11.08)
    place(W.plush["dog"], D0[0], D0[1]); dog_act(W, head_yaw=-18, head_pitch=3)
    lights(W)
    set_cam(W, *CHUTE_CAM)

def s3c(W, t, lt, dur):
    # the same view, later: another one. A jump cut, like a job done over and over
    present(W, [n for n in ALL if n not in ("clawd", "frog")])
    pass_to_chute(W, t, W.plush["frog2"], 11.42, 11.92, 12.08, 12.33)
    place(W.plush["dog"], D0[0], D0[1]); dog_act(W, head_yaw=-18 + 18 * ss(seg(t, 12.3, 12.7)), head_pitch=3)
    lights(W)
    set_cam(W, *CHUTE_CAM)

def s4(W, t, lt, dur):
    present(W, [n for n in ALL if n not in ("clawd", "frog", "frog2", "star")])
    dog = W.plush["dog"]; star = W.plush["star"]; star.hide(False)
    place(dog, D1[0], D1[1], 0, 0, 0)
    # someone walks past outside: its head follows, then comes back to the front
    hy = kf(t, [(12.83, 16), (13.6, 12), (14.5, -14), (14.9, -14), (15.5, 0)])
    dog_act(W, head_yaw=hy, head_pitch=4, ear_swing=3 * math.sin(t * 2.0), tail=10 * math.sin(t * 9) * seg(t, 13.2, 13.6) * (1 - seg(t, 14.2, 14.6)))
    # behind it the claw has the star, high enough to clear the others. It starts across, stops, and leans to look
    h, ga = grip(star)
    cx = kf(t, [(14.4, 0.185), (15.5, 0.0), (17.3, 0.0), (18.2, -0.12)])
    sw = 5 * math.sin(math.pi * seg(t, 15.2, 15.6)) * (1 if t < 15.6 else 0) + 5 * spring(t, 15.5, 1.3, 1.6) * (1 if t >= 15.5 else 0)
    tl = kf(t, [(15.9, 0), (16.4, 1), (17.1, 1), (17.5, 0)])
    jx, jy = jitter(W, t, 0.6)
    W.claw.pose(cx, 0.045, 0.262, open=ga, swing=(sw + jx + 4 * tl, jy - 9 * tl), tilt=(13 * tl, -9 * tl))
    hang(W, star, yaw=-10)
    W.person.c.hide_render = False                              # the passer-by, seen only as a reflection
    W.person.root.location = (kf(t, [(12.83, -1.3), (15.0, 1.4)], ease=lambda p: p), -1.15, -0.05)
    W.person.root.rotation_euler = Euler((0, 0, 0)); W.person.hand.location = (5, 5, 5)
    lights(W, bulbs=1.0 + 0.25 * ss(seg(t, 16.0, 17.2)))
    f = ss(seg(t, 15.0, 15.7)) * (1 - ss(seg(t, 17.2, 17.75)))
    focus = Vector((D1[0], D1[1] - 0.03, 0.09)).lerp(Vector((0.0, 0.03, 0.19)), f)
    push = ss(seg(t, 12.83, 17.9))
    set_cam(W, (0.225 - 0.01 * push, -0.84 + 0.03 * push, 0.125), (0.075, -0.08, 0.128), 88, 4.0, focus)

M5 = (0.195, 0.075)
M5_SPIN = -20                    # this close to the side glass the claw comes in turned, so no finger points at it
def s5a(W, t, lt, dur):
    present(W, ["dog", "octo", "mush", "cloud", "octo2", "mush2", "cloud2"])
    place(W.plush["mush"], M5[0], M5[1], 0, -10, 4)
    place(W.plush["octo2"], 0.120, 0.150, 0, -18, 0)
    place(W.plush["dog"], D1[0], D1[1]); dog_act(W, head_pitch=3)
    P = W.plush["octo"]
    deliver(W, t, P, REST["octo"][:2], 17.0, 17.4, 17.8, 17.92, 18.67, 18.83)
    lights(W)
    set_cam(W, *WIDE)

def s5b(W, t, lt, dur):
    present(W, ["dog", "mush", "cloud", "cloud2"])
    place(W.plush["dog"], D1[0], D1[1]); dog_act(W, head_pitch=3, head_yaw=-6)
    P = W.plush["mush"]
    h, ga = grip(P)
    src = (M5[0], M5[1], -10, 4)
    place(P, M5[0], M5[1], 0, -10, 4)
    x = kf(t, [(19.58, 0.02), (20.0, src[0])]); y = kf(t, [(19.58, -0.02), (20.0, src[1])])
    z = kf(t, [(19.9, 0.26), (20.33, h + 0.003), (20.6, h + 0.003), (21.4, 0.26)])
    o = kf(t, [(20.3, 55), (20.45, ga)], ease=eo)
    jx, jy = jitter(W, t, 0.6)
    W.claw.pose(x, y, z, open=o, swing=(4 * spring(t, 20.0, 1.6, 2.5) + jx, jy), spin=M5_SPIN * ss(seg(t, 19.58, 20.0)))
    if t > 20.5: hang(W, P, yaw=src[2] - M5_SPIN)
    lights(W, shop=0.55, morning=0.55)
    set_cam(W, *WIDE)

def s5c(W, t, lt, dur):
    present(W, ["dog", "cloud"])
    dog = W.plush["dog"]
    place(dog, D1[0], D1[1]); dog_act(W, head_pitch=4, head_yaw=10 * ss(seg(t, 21.5, 22.0)) * (1 - seg(t, 22.9, 23.2)), ear_swing=2 * math.sin(t * 2),
                                        tail=14 * math.sin(t * 2 * math.pi * 2.5) * seg(t, 21.6, 22.0) * (1 - seg(t, 22.7, 23.0)))
    h, ga = grip(dog)
    # the mitten is back on the glass: somebody is trying again. The claw comes down half way, opens half, thinks better of it
    z = kf(t, [(21.33, 0.29), (22.1, h + 0.07), (22.6, h + 0.07), (23.4, 0.27)])
    o = kf(t, [(21.9, 24), (22.25, 46), (22.45, 46), (22.7, 34), (23.2, 22)])
    jx, jy = jitter(W, t, 0.6)
    W.claw.pose(D1[0], D1[1] + 0.012, z, open=o, swing=(jx, jy), tilt=(0, 3 * seg(t, 22.0, 22.4)))
    hand_on_glass(W, ss(seg(t, 22.75, 23.5)) * 0.8)
    lights(W)
    p = ss(seg(t, 21.33, 23.33))
    a, b = Vector(WIDE[0]), Vector((0.06, -1.22, 0.16))
    ta, tb = Vector(WIDE[1]), Vector((0.095, -0.10, 0.130))
    set_cam(W, a.lerp(b, p), ta.lerp(tb, p), 64 + 16 * p, 4.0, (D1[0], D1[1], 0.09))

CORNER = (0.185, 0.125)
def s6(W, t, lt, dur):
    present(W, ["dog", "cloud"])
    dog = W.plush["dog"]; cloud = W.plush["cloud"]
    h, ga = grip(dog, 1.25)               # a gentle hold: barely touching
    SEAT, YAW = (0.185, 0.075), 8         # where it puts the dog, facing the front
    c0 = (0.045, 0.020)                   # cloud before the nudge
    c1 = (0.134, 0.012)                   # cloud after: between the dog and this camera
    LAY = -78                             # tipped onto its back, head against the wall
    # set down (-24.3), let go (-24.58), tip it onto its back (-25.17), slide the cloud in front (-26.1), pleased (-26.75), away
    k = claw_keys(t, [(23.33, dict(x=0.15, y=0.04, z=h + 0.09, open=ga)), (23.75, dict(x=SEAT[0], y=SEAT[1], z=h + 0.07)), (24.3, dict(z=h + 0.003)),
                      (24.33, dict(open=ga)), (24.58, dict(open=40, z=h + 0.003)), (24.72, dict(z=h + 0.085, x=SEAT[0], y=SEAT[1], open=-4)), (24.85, dict(x=SEAT[0] - 0.008, y=SEAT[1] - 0.122, z=h + 0.07)),
                      (24.95, dict(x=SEAT[0] - 0.008, y=SEAT[1] - 0.122, z=0.150)),                    # in front of its face
                      (25.08, dict(x=SEAT[0] - 0.008, y=SEAT[1] - 0.088, z=0.150)),                    # ...a push
                      (25.25, dict(x=SEAT[0] - 0.008, y=SEAT[1] - 0.100, z=0.165)), (25.5, dict(x=c0[0] - 0.080, y=c0[1], z=0.150, open=-6)),
                      (26.1, dict(x=c1[0] - 0.080, y=c1[1], z=0.150)), (26.25, dict(x=c1[0] - 0.095, y=c1[1] - 0.01, z=0.205, open=-6)),
                      (26.33, dict(open=26)), (26.5, dict(open=2)), (26.67, dict(open=20)), (26.83, dict(open=6, z=0.215)), (27.3, dict(x=0.03, y=0.105, z=0.272)), (28.5, dict(z=0.285, x=0.04, y=0.06, open=14))])
    jx, jy = jitter(W, t, 0.6)
    o = [k["open"]] * 3
    o[1] += kf(t, [(27.75, 0), (27.92, 26), (28.17, 26), (28.4, 8)])           # one finger lifts on its own: huh?
    W.claw.pose(k["x"], k["y"], k["z"], open=o, swing=(jx, jy), tilt=(kf(t, [(27.6, 0), (28.0, 9)]), 0))
    cp = kf(t, [(25.5, c0), (26.1, c1)])
    place(cloud, cp[0], cp[1], 0, -4 + 14 * seg(t, 25.5, 26.1), 0, roll=6 * math.sin(math.pi * seg(t, 25.5, 26.1)))
    if t < 24.33:
        hang(W, dog, yaw=YAW, tight=1.25, sq=-0.02)
        dog_act(W, ear_swing=6 * math.sin(t * 5) * (1 - seg(t, 23.8, 24.3)), head_yaw=0)
    else:
        # tipped over backwards (three drawings, a bounce); later it sits up on its own, looks, and leapfrogs the cloud
        lay = ei(seg(t, 25.0, 25.25)) - back(seg(t, 26.92, 27.17), 1.5)
        lean = LAY * lay + 6 * spring(t, 25.25, 2.4, 5.0) * (25.25 <= t < 26.9)
        hops = [(27.33, SEAT, YAW, 0.115, 0.25), (27.75, (0.082, -0.058), 0, 0.024, 0.17), (28.08, (0.104, -0.084), 0, 0.024, 0.17), (28.33, (0.122, -0.105), 0, 0, 0)]
        pos, yaw, hz = SEAT, YAW, 0.0
        for (ta, pa, ya, hh, hd), (tb, pb, yb, _, _) in zip(hops, hops[1:]):
            if t >= ta:
                p = seg(t, ta, ta + hd)
                pos = (lerp(pa[0], pb[0], p), lerp(pa[1], pb[1], p)); yaw = lerp(ya, yb, p)
                hz = hh * math.sin(math.pi * p)
        lands = [27.58, 27.92, 28.25]
        land = max([spring(t, tb, 2.5, 7.0) for tb in lands if t >= tb] or [0.0])
        crouch = 0.10 * math.sin(math.pi * seg(t, 27.17, 27.33))               # gathers itself before the big jump
        place(dog, pos[0], pos[1], hz + 0.030 * math.sin(math.radians(min(90.0, abs(lean)))), yaw, lean,
              sq=0.06 * spring(t, 24.33, 2.2, 5.0) * (t < 25.0) + crouch + 0.08 * land - 0.05 * (hz > 0.03))
        up = seg(t, 27.0, 27.17)
        dog_act(W, head_pitch=-10 * lay + 6 * up, head_yaw=-10 * up * (1 - seg(t, 27.33, 27.5)),
                ear_swing=-16 * (hz / 0.05 if hz < 0.05 else 1) * (hz > 0) + 9 * land + 14 * spring(t, 27.17, 2.0, 3.0) * (t > 27.17) - 12 * lay,
                perk=0.25 * up, ear_flap=14 * lay, tail=18 * math.sin(t * 2 * math.pi * 3) * seg(t, 27.6, 27.8))
    lights(W)
    p = ss(seg(t, 27.2, 28.4))
    set_cam(W, (-0.42, -1.05, 0.205), (0.135 - 0.02 * p, 0.060 - 0.07 * p, 0.108), 98, 4.0, (0.16, 0.08 - 0.10 * p, 0.10))

def s7a(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]
    hops = [(28.42, (0.122, -0.105)), (28.75, (0.124, -0.128)), (29.17, D1), (29.58, D1)]
    pos, hz = hops[0][1], 0.0
    for (ta, pa), (tb, pb) in zip(hops, hops[1:]):
        if t >= ta:
            p = seg(t, ta, ta + 0.17)
            pos = (lerp(pa[0], pb[0], p), lerp(pa[1], pb[1], p)); hz = 0.022 * math.sin(math.pi * p)
    land = max([spring(t, tb + 0.17, 2.5, 7.0) for (tb, _) in hops[:-1] if t >= tb + 0.17] or [0.0])
    place(dog, pos[0], pos[1], hz, 0, 0, sq=0.05 * land)
    dog_act(W, ear_swing=-14 * (hz / 0.022) + 8 * land, head_pitch=4 * seg(t, 29.7, 30.2))
    # the claw trails after it in little starts and stops
    steps = [(28.42, (0.04, 0.06)), (29.0, (0.04, 0.06)), (29.4, (0.075, -0.01)), (29.9, (0.075, -0.01)), (30.4, (0.10, -0.060))]
    cp = kf(t, steps)
    sw = 4 * spring(t, 29.4, 1.5, 2.2) * (t >= 29.4) + 4 * spring(t, 30.4, 1.5, 2.2) * (t >= 30.4)
    jx, jy = jitter(W, t, 0.6)
    W.claw.pose(cp[0], cp[1], kf(t, [(28.42, 0.30), (30.8, 0.275)]), open=14, swing=(jx, sw + jy), tilt=(0, -6 * seg(t, 30.4, 30.9)))
    b = 1.0 + 0.5 * max(0.0, 1 - abs(t - 28.92) / 0.25)
    lights(W, bulbs=b)
    set_cam(W, *WIDE)

PROFILE_CAM = ((0.86, -0.085, 0.135), (0.125, -0.128, 0.140), 54, 4.0)        # the dog left of centre with the front glass beyond it, the claw to the right
BACK34_CAM = ((0.86, 0.17, 0.150), (0.125, -0.115, 0.140), 55, 4.0)       # from behind its right shoulder, through the side glass
def s7b(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]
    place(dog, D1[0], D1[1]); dog_act(W, head_pitch=5, ear_swing=2 * math.sin(t * 2.2))
    # comes down behind it to the height of its head; cocks one way, the other; then leans to look where it is looking
    z = kf(t, [(31.0, 0.275), (31.75, 0.150)])
    tx = kf(t, [(31.83, 0), (32.08, 11), (32.5, 11), (32.75, -11), (33.08, -11), (33.33, 0)])
    ty = kf(t, [(33.17, 0), (33.6, -14)])
    jx, jy = jitter(W, t, 0.6)
    W.claw.pose(D1[0], -0.045, z, open=kf(t, [(31.0, 14), (33.2, 14), (33.6, 22)]), swing=(jx, jy + 3 * spring(t, 31.75, 1.4, 2.0) * (t > 31.75)), tilt=(tx, ty))
    lights(W)
    p = ss(seg(t, 31.0, 33.75))
    pos, tgt, lens, fs = PROFILE_CAM
    set_cam(W, (pos[0] - 0.04 * p, pos[1], pos[2]), tgt, lens, fs, (D1[0], -0.10, 0.10))

def person_at_glass(W, t, t_in, t_press):
    """The person walks up and puts a mitten on the glass, on the old hand print."""
    W.person.c.hide_render = False
    a = ss(seg(t, t_in, t_press - 0.25))
    W.person.root.location = Vector((0.85, -1.1, -0.06)).lerp(Vector((0.36, -0.52, -0.06)), a)
    W.person.root.rotation_euler = Euler((0, 0, math.radians(12)))
    h = eo(seg(t, t_press - 0.5, t_press))
    W.person.hand.location = Vector((0.42, -0.55, -0.06)).lerp(HAND_ON, h) + Vector((0, -0.02 * math.sin(math.pi * h), 0.012 * math.sin(math.pi * h)))
    W.person.hand.rotation_euler = Euler((math.radians(-8), math.radians(lerp(-40, -14, h)), 0))
    W.person.wrist.rotation_euler = Euler((math.radians(-42), 0, 0))
    spill(W, HAND_ON + Vector((0, -0.02, 0)), 2.0)

def s8a(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]
    person_at_glass(W, t, 33.5, 34.67)
    hop = math.sin(math.pi * seg(t, 35.08, 35.25)) * (1 if t < 35.25 else 0) + math.sin(math.pi * seg(t, 35.42, 35.58)) * (1 if 35.42 < t < 35.58 else 0)
    place(dog, D1[0], D1[1] - 0.004 * seg(t, 35.0, 35.3), 0.012 * hop, 0, -6 * seg(t, 34.9, 35.2), sq=-0.05 * hop + 0.04 * spring(t, 35.6, 2.5, 6) * (t > 35.6))
    perk = back(seg(t, 34.83, 35.08))
    dog_act(W, head_pitch=5 + 12 * ss(seg(t, 34.7, 35.0)), head_yaw=-4, perk=0.75 * perk, tail=26 * math.sin(t * 2 * math.pi * 3.0) * seg(t, 35.0, 35.2), ear_swing=-8 * hop)
    jx, jy = jitter(W, t, 0.6)
    W.claw.pose(D1[0] - 0.100, -0.045, 0.165, open=22, swing=(jx, jy), tilt=(-8, -12))
    lights(W)
    p = ss(seg(t, 33.75, 35.92))
    set_cam(W, (0.236, 0.185, 0.125 + 0.006 * p), (0.150, -0.20, 0.092), 36, 2.8, (D1[0], D1[1], 0.11))

def s8b(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]
    person_at_glass(W, 36.0, 33.5, 34.67)
    place(dog, D1[0], D1[1] - 0.004, 0, 0, -6)
    dog_act(W, head_pitch=17, perk=0.75, tail=26 * math.sin(t * 2 * math.pi * 3.0))
    # the three of them in one frame. It understands: the fingers fall open one by one, the cord goes slack,
    # the hub sinks and hangs its head; the lights blink and stay lower
    d = ss(seg(t, 36.25, 37.25))
    jx, jy = jitter(W, t, 0.4)
    sway = 2.2 * math.sin((t - 36.25) * 2.6) * d
    W.claw.pose(D1[0] - 0.100, -0.045, 0.165 - 0.038 * d, open=[22 + 24 * ss(seg(t, 36.25, 36.9)), 22 + 20 * ss(seg(t, 36.42, 37.1)), 22 + 26 * ss(seg(t, 36.58, 37.3))],
                swing=(sway + jx, jy), tilt=(-8 * (1 - d), -12 * (1 - d) + 9 * d), slack=d)
    blink = 0.4 if (36.5 <= t < 36.59 or 36.75 <= t < 36.84) else 1.0
    lights(W, bulbs=blink * (1.0 - 0.38 * seg(t, 36.9, 37.4)), key=(0.6 + 0.4 * blink) * (1.0 - 0.30 * seg(t, 36.9, 37.4)))
    p = ss(seg(t, 35.92, 37.58))
    pos, tgt, lens, fs = BACK34_CAM
    set_cam(W, (pos[0] - 0.03 * p, pos[1], pos[2]), (0.06, -0.135, 0.128), lens + 3, fs, (D1[0] - 0.06, -0.06, 0.13))

def s8c(W, t, lt, dur):
    present(W, [])
    W.person.c.hide_render = False
    W.person.root.location = (0.9, -0.75, -0.3)
    cp = W.machine.coin_pos + Vector((0, 0, 0))
    a = eo(seg(t, 37.58, 38.25)); b = ss(seg(t, 38.25, 38.5)); c = ss(seg(t, 38.58, 39.0))
    # the mitten comes in from the right with the coin held between thumb and palm, and pushes it home
    hand = Vector((0.40, -0.40, -0.23)).lerp(cp + Vector((0.060, -0.032, -0.002)), a) + Vector((0, 0.022, 0)) * b + Vector((0.07, -0.05, -0.02)) * c
    W.person.hand.location = hand
    W.person.hand.rotation_euler = Euler((math.radians(6), math.radians(90), math.radians(180 - 14 * (1 - a))), "XYZ")
    coin = W.coin
    coin.hide_render = t >= 38.5
    coin.location = hand + Vector((-0.060, 0.010, 0.002))
    coin.rotation_euler = Euler((0, math.radians(90), 0))
    lamp = 1.5 + 14 * max(0.0, 1 - abs(t - 38.6) / 0.25) + 4 * seg(t, 38.5, 38.6)
    M.set_emit(W.machine.coin_lamp, lamp)
    M.set_emit(W.machine.btn_mat, 0.6 + 3.0 * seg(t, 38.5, 38.7))
    W.machine.coin_light.energy = 2.2
    W.claw.pose(0, 0, Z_HI)
    lights(W, bulbs=0.68, key=0.75)
    set_cam(W, (-0.16, -0.70, -0.125), (cp.x + 0.022, cp.y, cp.z - 0.004), 85, 4.0, (cp.x, cp.y - 0.008, cp.z))

def s9a(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]
    person_at_glass(W, 36.0, 33.5, 34.67)
    h, ga = grip(dog, 0.80)                # a real grip: the tips sink into the fur
    # it gathers itself back from the glass, where there is room to open right out; then swoops in, fingers folding as the glass gets near
    WIND = (D1[0] - 0.045, -0.060)
    a = ss(seg(t, 38.92, 39.3)); b = ss(seg(t, 39.5, 39.83)) ** 1.5      # four drawings down: fast, but not a pop
    cx = lerp(lerp(D1[0] - 0.100, WIND[0], a), D1[0], b); cy = lerp(lerp(-0.045, WIND[1], a), D1[1] + 0.004, b)
    z = lerp(lerp(0.127, 0.240, a), h, b)
    if t > 40.4: z = h + 0.05 * ss(seg(t, 40.4, 40.75))
    o = kf(t, [(38.92, 46), (39.2, 70), (39.75, 70), (39.92, ga), (40.0, ga - 3), (40.1, ga)], ease=eo)
    jx, jy = jitter(W, t, 0.3)
    W.claw.pose(cx, cy, z, open=o, swing=(jx * (t < 39.4), 0), slack=1 - seg(t, 38.92, 39.15))
    sq = 0.10 * max(0.0, 1 - abs(t - 39.96) / 0.12)
    if t < 40.4:
        place(dog, D1[0], D1[1] - 0.004, 0, 0, -6 * (1 - seg(t, 39.9, 40.0)), sq=sq - 0.05 * seg(t, 39.92, 40.1))
    else:
        hang(W, dog, yaw=0, tight=0.80, sq=-0.05)
    dog_act(W, head_pitch=17 - 14 * seg(t, 39.85, 40.0), perk=0.75 - 0.5 * seg(t, 39.85, 40.0) + 0.3 * seg(t, 40.1, 40.4),
            tail=26 * math.sin(t * 2 * math.pi * 3.0) * (1 - seg(t, 39.8, 39.95)), ear_swing=-12 * seg(t, 40.4, 40.7))
    lights(W, bulbs=lerp(0.68, 1.25, ss(seg(t, 38.92, 39.3))), key=lerp(0.75, 1.1, ss(seg(t, 38.92, 39.3))))
    pos, tgt, lens, fs = BACK34_CAM
    set_cam(W, (pos[0] - 0.03, pos[1], pos[2] + 0.02), (0.10, -0.155, 0.160), lens - 8, fs, (D1[0], -0.14, 0.13))

def s9b(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]
    h, ga = grip(dog, 0.80)
    zc = h + 0.105
    z = kf(t, [(40.58, h + 0.02), (41.33, zc)])
    p = ss(seg(t, 41.33, 44.0))
    x = lerp(D1[0], CH[0], p); y = lerp(D1[1] + 0.004, CH[1], p)
    W.claw.pose(x, y, z, open=ga, swing=(0, 0), spin=CH_SPIN * p)
    look = ss(seg(t, 42.0, 42.6))
    hang(W, dog, yaw=-10 * look - CH_SPIN * p, tight=0.80, sq=-0.05)
    v = math.sin(math.pi * seg(t, 41.33, 44.0))
    dog_act(W, head_pitch=3 + 30 * look, head_yaw=8 * look, perk=0.3, ear_swing=-10 * (1 - seg(t, 40.58, 41.3)) - 6 * look, ear_flap=10 * v, tail=20 * math.sin(t * 2 * math.pi * 2.5) * look)
    lights(W, bulbs=1.25, key=1.1)
    px = lerp(D1[0], CH[0], 0.5) + (x - lerp(D1[0], CH[0], 0.5)) * 0.55
    set_cam(W, (-0.02, -1.25, 0.225), (px, -0.10, 0.205), 76, 3.2, (x, y, 0.20))

def s10a(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]
    h, ga = grip(dog, 0.80)
    zc = h + 0.105
    hug = kf(t, [(44.58, 0), (44.83, 1), (45.5, 1), (45.75, 0.3)])
    o = ga - 4.5 * hug
    rel = 45.83
    if t >= rel: o = lerp(ga, 72, eo(seg(t, rel, rel + 0.17)))
    W.claw.pose(CH[0], CH[1], zc - 0.006 * hug, open=o, swing=(0, 1.2 * spring(t, rel, 1.2, 1.2) * (t > rel)), tilt=(0, -5 * hug), spin=CH_SPIN)
    if t < rel + 0.04:
        hang(W, dog, yaw=-10 - CH_SPIN, tight=0.80, sq=-0.05 - 0.03 * hug)
        dog_act(W, head_pitch=33, head_yaw=8, perk=0.3 + 0.3 * hug, tail=20 * math.sin(t * 2 * math.pi * 2.5), ear_swing=-6)
    else:
        zf = fall(t, rel + 0.04, zc - h, g=2.6)
        place(dog, CH[0], CH[1], zf, -10, 0, sq=-0.06)
        dog_act(W, head_pitch=33, head_yaw=8, perk=0.95, ear_flap=10, tail=0)
        if zf < -0.2: dog.hide(True)
    lights(W, bulbs=1.25, key=1.1)
    set_cam(W, (-0.305, -0.86, 0.225), (CH[0] + 0.005, CH[1], 0.185 - 0.02 * math.sin(math.pi * seg(t, 45.85, 46.4)) + 0.085 * ss(seg(t, 46.25, 46.9))), 100, 2.8, (CH[0], CH[1] - 0.02, 0.19))

BOARD = 97.5                                       # the open door flap rests on the tray's front edge at this angle
BIN_LAMP = 0.07
def board_top(W, s):
    """A point on the open flap's upper face, s metres out from the hinge."""
    h = W.machine.flap.location; a = math.radians(BOARD)
    return Vector((h.x, h.y - s * math.sin(a) + 0.0015 * math.cos(a), h.z + s * math.cos(a) + 0.0015 * math.sin(a)))

def s10b(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]; Mx = W.machine
    dc = Mx.door_c
    F = lambda f: f / 12.0                           # this shot is timed in drawings (568-592)
    even = lambda p: p
    # the prize door is a little drawbridge. A knock from inside, a push, and it falls open on the tray's edge:
    # the dog is sitting in the bin. It ducks out under the lintel onto the board; a mitten is held out at the
    # board's end, palm up; it hops on, and is lifted away. The flap never has to pass anything.
    Mx.flap.rotation_euler.x = math.radians(kf(t, [(F(568), 0), (F(569), 4), (F(570), 1), (F(571), 10), (F(572), 40), (F(573), 80), (F(574), BOARD),
                                                   (F(575), BOARD - 7), (F(576), BOARD)], even))
    Mx.bin_lamp.energy = BIN_LAMP
    seat_in = Vector((dc.x, Y0 + 0.052, Mx.bin_floor_z))           # far enough back that its paws are behind the front panel
    seat_out = board_top(W, 0.052) + Vector((0.004, 0, 0))
    palm = Vector((dc.x + 0.008, Mx.flap.location.y - 0.185, -0.494))      # its top is level with the board's tip
    hin = eo(seg(t, 48.0, 48.42))
    lift = ei(seg(t, 48.83, 49.5))
    dip = 0.010 * spring(t, 48.75, 2.4, 6.0) * (t >= 48.75)
    hpos = (palm + Vector((0.10, -0.20, -0.16))).lerp(palm, hin) + Vector((0.07, -0.06, 0.42)) * lift - Vector((0, 0, dip))
    W.person.c.hide_render = False
    W.person.root.location = (0.3, -0.95, -0.5)
    W.person.hand.location = hpos
    W.person.hand.rotation_euler = Euler((math.radians(90 - 8 * lift), 0, math.radians(180 - 10 + 10 * hin)), "XYZ")       # palm up, fingers toward the door
    W.person.wrist.rotation_euler = Euler((math.radians(-28), 0, 0))
    out = seg(t, F(577), F(579))                     # the hop out of the bin
    hop = seg(t, 48.58, 48.75)                       # the hop onto the palm
    if t < 48.58:
        # it knocks with its head: it rocks forward onto its front paws
        nudge = kf(t, [(F(568), 0), (F(569), 0.004), (F(570), 0.001), (F(571), 0.004), (F(572), 0.002), (F(574), 0)], even)
        lean = kf(t, [(F(568), 3), (F(569), 26), (F(570), 10), (F(571), 33), (F(572), 16), (F(574), 3), (F(576), 6), (F(577), 10), (F(578), 24), (F(579), 6), (F(581), 0)], even)
        sq = kf(t, [(F(576), 0), (F(577), 0.14), (F(578), 0.12), (F(579), 0.14), (F(580), -0.03), (F(581), 0), (F(582), 0), (F(583), 0.10)], even)
        pos = seat_in.lerp(seat_out, ss(out)) + Vector((0, -nudge, 0.014 * math.sin(math.pi * out)))
    else:
        pos = seat_out.lerp(hpos + Vector((0, 0.010, 0.016)), hop) + Vector((0, 0, 0.026 * math.sin(math.pi * hop)))
        lean = 8 * math.sin(math.pi * hop)
        sq = 0.10 * (1 - seg(t, 48.58, 48.67)) + 0.07 * spring(t, 48.75, 2.5, 6) * (t >= 48.75)
    place(dog, pos.x, pos.y, pos.z + 0.006 + 0.036 * math.sin(math.radians(lean)), 6 * lift, lean, sq=sq)        # leaning, it rocks onto its front paws
    look = ss(seg(t, F(580), F(583)))
    dog_act(W, head_pitch=4 + 6 * seg(t, F(574), F(575)) + 20 * look, head_yaw=-6 * look, perk=0.05 + (0.35 + 0.2 * math.sin(t * 6)) * seg(t, F(579), F(581)),         # ears stay down in the bin: the shaft is narrow
            tail=30 * math.sin(t * 2 * math.pi * 3.2) * seg(t, F(574), F(576)),
            ear_swing=8 * spring(t, F(574), 2.0, 3.0) * (t >= F(574)) + 10 * spring(t, F(579), 2.0, 3.0) * (t >= F(579)) - 12 * math.sin(math.pi * hop) + 10 * spring(t, 48.75, 2.0, 3.0) * (t > 48.75))
    W.claw.pose(CH[0], CH[1], 0.27, open=72, spin=CH_SPIN)
    lights(W, bulbs=1.1)
    set_cam(W, (0.03, -1.00, -0.37), (dc.x + 0.02, dc.y - 0.03, dc.z - 0.045 + 0.045 * ss(seg(t, 48.9, 49.4))), 50, 4.0, (pos.x, pos.y - 0.03, pos.z + 0.08))

MEET = Vector((-0.020, Y0, 0.130))                 # the spot on the glass where they say goodbye
TOUCH = dict(x=-0.020, y=-0.086, z=0.192)          # the claw's place for it: one finger just reaches the glass
def s10c(W, t, lt, dur):
    present(W, ["dog"])
    dog = W.plush["dog"]
    # outside now: held up to the glass in the mitten, its nose against it, looking in
    away = ss(seg(t, 51.08, 51.7))
    held = Vector((MEET.x, Y0 - 0.050, 0.046)) + Vector((0.05, -0.16, -0.10)) * away
    W.person.c.hide_render = False
    W.person.root.location = (0.06, -0.66, -0.08)
    W.person.root.rotation_euler = Euler((0, 0, math.radians(8)))
    spill(W, held + Vector((0, 0, 0.08)), 3.0)
    W.person.hand.location = held + Vector((0, -0.047, 0.035))
    W.person.hand.rotation_euler = Euler((math.radians(-6), 0, 0))
    W.person.wrist.rotation_euler = Euler((math.radians(-35), 0, 0))
    touch = ss(seg(t, 50.0, 50.5))
    nuzzle = ss(seg(t, 50.5, 50.75)) * (1 - away)
    place(dog, held.x, held.y, held.z + 0.006, 180, 5 * nuzzle, sq=0)
    dog_act(W, head_pitch=14 - 6 * nuzzle, head_roll=7 * nuzzle, perk=0.35 + 0.4 * touch, tail=28 * math.sin(t * 2 * math.pi * 3.0), ear_swing=3 * math.sin(t * 3))
    # the claw hurries over from the chute, comes down, and puts one finger out to the glass
    arr = eo(seg(t, 49.42, 50.0))
    x = lerp(-0.13, TOUCH["x"], arr); z = lerp(0.27, TOUCH["z"], ss(seg(t, 49.5, 50.08)))
    sw = -6 * (1 - arr) + 5 * spring(t, 50.0, 1.5, 2.6) * (t >= 50.0)
    jx, jy = jitter(W, t, 0.3)
    reach = 14 + 40 * back(seg(t, 50.08, 50.5), 1.2)
    W.claw.pose(x, TOUCH["y"], z, open=[reach, 12, 12], swing=((sw + jx) * (1 - touch), 0), tilt=(0, -5 * touch), spin=180)
    lights(W, bulbs=1.1 + 0.2 * nuzzle, key=1.05)
    pos, tgt, lens, fs = BACK34_CAM
    p = ss(seg(t, 49.42, 51.58))
    set_cam(W, (pos[0] - 0.04 * p, pos[1], pos[2]), (-0.010, -0.160, 0.150), 78, fs, (MEET.x, -0.17, 0.13))

DROOP = dict(x=TOUCH["x"], y=TOUCH["y"], z=0.180)        # it sags where it stood, at the glass
def droop_pose(W, t, t0, amp=6.0, up=0.0):
    """Hanging with nothing to do: fingers loose, head down, the cord slack, swinging less and less."""
    d = max(0.0, t - t0)
    sw = amp * math.exp(-0.34 * d) * math.cos(2 * math.pi * 0.62 * d) * (t >= t0)
    W.claw.pose(DROOP["x"], DROOP["y"], DROOP["z"] + 0.060 * up, open=[lerp(38, 14, up), lerp(30, 14, up), lerp(43, 14, up)], swing=(sw * (1 - up), 0.3 * sw * (1 - up)),
                tilt=(7 * (1 - up), 5 * (1 - up)), slack=1 - up, spin=180)

def s11(W, t, lt, dur):
    present(W, [])
    # it is still at the glass with one finger out. The finger slides off; it sags; the shop goes dark in three steps,
    # the bulbs go out one after another, and one is left
    g = ss(seg(t, 52.0, 52.75))
    if g < 1:
        W.claw.pose(lerp(TOUCH["x"], DROOP["x"], g), lerp(TOUCH["y"], DROOP["y"], g), lerp(TOUCH["z"], DROOP["z"], g),
                    open=[lerp(54, 38, g), lerp(12, 30, g), lerp(12, 43, g)], tilt=(7 * g, lerp(-5, 5, g)), slack=g, spin=180)
    else:
        droop_pose(W, t, 52.75)
    shop = 1.0 - 0.34 * (t >= 51.83) - 0.33 * (t >= 52.17) - 0.33 * (t >= 52.5)
    order = [0, 17, 8, 9, 4, 13, 2, 15, 6, 11, 1, 16, 7, 10, 3, 14, 5, 12]
    bulbs = [1.0] * 18
    for i, b in enumerate(order):
        if t >= 52.42 + i * 0.06: bulbs[b] = 0.0
    k = 1 - seg(t, 52.42, 53.6)
    lights(W, key=0.02 + 0.98 * k * k, bulbs=bulbs, last=ss(seg(t, 53.0, 53.6)), shop=max(0.0, shop))
    set_cam(W, *WIDE)

NEW = [("frog", (0.115, -0.125, -8)), ("star2", (-0.060, 0.100, 10)), ("octo", (-0.190, 0.070, 14)), ("mush", (0.205, 0.085, -8)), ("cloud", (0.070, 0.125, 4)),
       ("frog2", (0.135, 0.000, 18)), ("star", (0.205, -0.070, -14)), ("octo2", (-0.165, 0.150, 6)), ("mush2", (-0.160, -0.005, -6)), ("cloud2", (0.000, 0.065, 10))]
CLAWD_NEW = (0.125, -0.062)                # on top of the two frogs, to the claw's right
def s12(W, t, lt, dur):
    names = [n for n, _ in NEW] + ["clawd2"]
    present(W, names)
    for i, (n, (x, y, yaw)) in enumerate(NEW):
        P = W.plush[n]
        t0 = 54.95 + i * 0.085                       # lets go
        tl = t0 + 0.42                               # lands
        if t < t0: P.hide(True); continue
        p = seg(t, t0, tl)
        z = 0.52 * (1 - p * p)
        b = spring(t, tl, 2.6, 5.5) * (t >= tl)
        place(P, x, y + 0.02 * (1 - p), z + 0.012 * abs(b) , yaw + 70 * (1 - p), (30 + 20 * hsh(n)) * (1 - p) + (10 * hsh(n, 2) - 5) + 6 * b,
              roll=(40 * hsh(n, 3) - 20) * (1 - p), sq=0.10 * b)
    C = W.plush["clawd2"]
    t0, tl = 55.71, 56.13                            # the last one down, on the beat
    if t < t0: C.hide(True)
    else:
        p = seg(t, t0, tl)
        b = spring(t, tl, 2.4, 4.2) * (t >= tl)
        place(C, CLAWD_NEW[0], CLAWD_NEW[1], 0.052 + 0.50 * (1 - p * p) + 0.016 * abs(b), -6 + 50 * (1 - p), 4 + 25 * (1 - p) + 7 * b, roll=-5 + 5 * b, sq=0.12 * b)
    up = ss(seg(t, 56.33, 56.67))
    droop_pose(W, t, 52.75, up=up)
    st = W.claw.state
    o = 14 + kf(t, [(56.75, 0), (56.92, 24), (57.08, 0), (57.25, 6), (58.5, 6)])
    if up > 0:
        # it lifts its head and turns to the new arrival
        W.claw.pose(st["x"], st["y"], st["z"], open=[lerp(a, o, up) for a in (38, 30, 43)], swing=st["swing"], tilt=(lerp(7, 12, up), lerp(5, 2, up)), slack=1 - up, spin=180)
    order = [0, 9, 1, 10, 2, 11, 3, 12, 4, 13, 5, 14, 6, 15, 7, 16, 8, 17]
    bulbs = [0.0] * 18
    for i, b in enumerate(order):
        if t >= 54.67 + i * 0.022: bulbs[b] = 1.0 + 0.5 * max(0.0, 1 - (t - 54.67 - i * 0.022) / 0.2)
    lights(W, key=ss(seg(t, 54.67, 55.1)), bulbs=bulbs, last=1 - seg(t, 54.67, 55.0), shop=0.25, morning=1.0)
    p = ss(seg(t, 54.58, 58.5))
    set_cam(W, (0.012, -1.50 + 0.05 * p, 0.215), WIDE[1], 64, 3.2, (0.05, -0.05, 0.10))

FUNCS = dict(s1=s1, s2=s2, s3a=s3a, s3b=s3b, s3c=s3c, s4=s4, s5a=s5a, s5b=s5b, s5c=s5c, s6=s6, s7a=s7a, s7b=s7b, s8a=s8a, s8b=s8b, s8c=s8c,
             s9a=s9a, s9b=s9b, s10a=s10a, s10b=s10b, s10c=s10c, s11=s11, s12=s12)

def pose(W, t, cam=None):
    name, t0, t1 = shot_at(t)
    # defaults every shot starts from
    W.person.c.hide_render = True
    W.person.root.rotation_euler = Euler((0, 0, 0))
    W.coin.hide_render = True
    W.machine.flap.rotation_euler.x = 0
    M.set_emit(W.machine.coin_lamp, 1.5); M.set_emit(W.machine.btn_mat, 0.6)
    W.machine.coin_light.energy = 0.0
    W.machine.bin_lamp.energy = 0.0
    W.machine.spill.energy = 0.0
    W.person.wrist.rotation_euler = Euler((0, 0, 0))
    dog_act(W)
    FUNCS[name](W, t, t - t0, t1 - t0)
    if cam == "wide": set_cam(W, *WIDE)
    return name
