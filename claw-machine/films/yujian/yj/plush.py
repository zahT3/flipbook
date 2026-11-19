"""The plush cast. Every builder returns a Plush: root empty at the seat point, facing -Y."""
import bpy, bmesh, math, random
from mathutils import Vector, Euler
from .common import *
from . import mats as M

FUR_Q = float(arg("--furq", "1.0"))     # strand count multiplier (previews use less)

class Plush:
    def __init__(self, name, c):
        self.name = name
        self.c = coll("plush_" + name, c)
        self.root = empty(name, self.c)
        self.sq = empty(name + "_sq", self.c, self.root)       # squash/stretch lives here
        self.p = {}                                             # named parts for acting
        self.h = 0.1                                            # height, for grabbing
        self.grab = 0.05                                        # z of the grab point above the seat
        self.rad = 0.04                                         # horizontal radius for the fingers to close on
        self.kind = name
    def hide(self, on):
        self.c.hide_render = on; self.c.hide_viewport = on

_mc = {}
def cached(key, make):
    if key not in _mc: _mc[key] = make()
    return _mc[key]

def mesh_area(me): return sum(p.area for p in me.polygons)

def add_fur(o, fur_mat, length=0.0028, density=260000, children=24, seed=1, rand=0.6, rough=(0.0012, 0.0008, 0.0018), clump=0.0, kink=None, rad=0.14):
    """Short wool strands on a mesh. density = parent strands per square metre."""
    o.data.materials.append(fur_mat)
    md = o.modifiers.new("fur", "PARTICLE_SYSTEM")
    ps = md.particle_system; s = ps.settings
    s.type = "HAIR"
    s.count = max(50, int(mesh_area(o.data) * density * FUR_Q))
    s.hair_step = 3
    s.emit_from = "FACE"
    s.distribution = "RAND"
    s.use_emit_random = True
    s.hair_length = length                 # also sets normal_factor (= length / 4)
    s.factor_random = rand * length / 4
    s.child_type = "INTERPOLATED"
    s.rendered_child_count = children
    s.child_percent = 2
    s.child_length = 1.0
    s.clump_factor = clump
    s.roughness_1 = rough[0]; s.roughness_1_size = 0.4
    s.roughness_endpoint = rough[1]
    s.roughness_2 = rough[2]; s.roughness_2_size = 0.3
    if kink:
        s.kink = "CURL"; s.kink_amplitude = kink[0]; s.kink_frequency = kink[1]
    s.render_step = 3
    s.display_step = 2
    s.radius_scale = 0.001
    s.root_radius = rad; s.tip_radius = rad * 0.35
    s.material = len(o.data.materials)
    ps.seed = seed
    return ps

def fuzz(o, fur_mat, length=0.0012, density=180000, children=10, seed=1):
    """Felt fuzz: few, very short stray fibres."""
    return add_fur(o, fur_mat, length, density, children, seed, rand=1.2, rough=(0.0006, 0.0004, 0.001), rad=0.09)

def stitches(name, path, c, parent, m, n=60, dash=0.0038, gap=0.0026, r=0.00065, closed=False):
    """Running stitch along path(u), u in 0..1 (parent-local points)."""
    pts = [Vector(path(i / n)) for i in range(n + 1)]
    lens = [0.0]
    for a, b in zip(pts, pts[1:]): lens.append(lens[-1] + (b - a).length)
    total = lens[-1]
    def at(d):
        d = clamp(d, 0, total)
        for i in range(len(pts) - 1):
            if lens[i + 1] >= d:
                k = (d - lens[i]) / max(1e-9, lens[i + 1] - lens[i])
                return pts[i].lerp(pts[i + 1], k)
        return pts[-1]
    bm = bmesh.new()
    d = gap * 0.5
    tmp = []
    while d + dash < total:
        seg_pts = [at(d + dash * k / 3) for k in range(4)]
        tmp.append(seg_pts); d += dash + gap
    bm.free()
    meshes = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for seg_pts in tmp:
        me = tube_mesh("tmp", seg_pts, [r * 0.6, r, r, r * 0.6], None, sides=6)
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    bm.to_mesh(meshes); bm.free()
    for p in meshes.polygons: p.use_smooth = True
    meshes.materials.append(m)
    return new_obj(name, meshes, c, parent)

def bead(name, r, c, parent, loc, m=None):
    m = m or cached("bead", lambda: M.plain("bead", "#0b0908", rough=0.12, coat=1.0, spec=0.8))
    return ell(name, (r, r * 0.8, r), c, loc, m, parent, u=24, v=16)

def button(name, r, c, parent, loc, col="#3b2a20", rot=(90, 0, 0), thread_col="#e9dcc3"):
    """Four-hole button with a cross of thread."""
    m = cached("btn" + col, lambda: M.plain("btn" + col, col, rough=0.3, coat=0.5))
    mt = cached("thr" + thread_col, lambda: M.thread("thr" + thread_col, thread_col))
    mh = cached("btnhole", lambda: M.plain("btnhole", "#0a0806", rough=0.9))
    o = empty(name, c, parent, loc)
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    disc = cyl(name + "_d", r, r, r * 0.3, c, m=m, parent=o, seg_n=28)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, segments=28, radius1=r * 0.82, radius2=r * 0.82, depth=r * 0.12, cap_ends=False)
    rim = new_obj(name + "_rim", finish(bm, name + "_rim", m), c, o, (0, 0, r * 0.2))
    rim.modifiers.new("s", "SOLIDIFY").thickness = r * 0.16
    h = r * 0.3
    for i, (x, y) in enumerate(((h, h), (-h, h), (h, -h), (-h, -h))):
        cyl(name + "_h%d" % i, r * 0.13, r * 0.13, r * 0.34, c, (x, y, 0.0002), mh, o, seg_n=10)
    for i, (a, b) in enumerate((((h, h), (-h, -h)), ((-h, h), (h, -h)))):
        new_obj(name + "_t%d" % i, tube_mesh("t", [(a[0], a[1], r * 0.17), (0, 0, r * 0.26), (b[0], b[1], r * 0.17)], r * 0.09, mt, sides=6), c, o)
    return o

def on_ell(radii, d, lift=0.0):
    """Point on an ellipsoid surface in direction d, lifted along the normal."""
    d = Vector(d).normalized()
    k = 1 / math.sqrt((d.x / radii[0]) ** 2 + (d.y / radii[1]) ** 2 + (d.z / radii[2]) ** 2)
    p = d * k
    n = Vector((p.x / radii[0] ** 2, p.y / radii[1] ** 2, p.z / radii[2] ** 2)).normalized()
    return p + n * lift

def cheek_mat(): return cached("cheek", lambda: M.plain("cheek", "#E79A8E", rough=0.95, sheen=0.8, noise_bump=0.6, noise_scale=1500))
def thread_mat(col): return cached("thr" + col, lambda: M.thread("thr" + col, col))

# ================================================================ the dog (hero)
CREAM, RUST = "#FFE8BC", "#B4633A"
def build_dog(c):
    P = Plush("dog", c); pc = P.c
    P.h, P.grab, P.rad = 0.125, 0.085, 0.040
    body_r = (0.037, 0.033, 0.039)
    head_r = (0.041, 0.037, 0.036)
    patch = [((0.017, -0.030, 0.006), 0.0165, RUST, 0.10)]
    fab_body = M.fabric("dog_body", CREAM, "polar_fleece", tex_amt=0.25)
    fur_body = M.fur("dog_fur", CREAM, vary=0.10, tip_light=0.15)
    fab_head = M.fabric("dog_head", CREAM, "polar_fleece", patches=patch, tex_amt=0.25)
    fur_head = M.fur("dog_fur_head", CREAM, patches=patch, vary=0.10, tip_light=0.15)
    fab_rust = M.fabric("dog_rust", RUST, "polar_fleece")
    fur_rust = M.fur("dog_fur_rust", RUST)
    fur_muzz = M.fur("dog_fur_muzz", "#FBF4E4")
    def pear(q, p):
        k = 1 + 0.20 * (-p.z) - 0.05 * p.z * p.z
        return Vector((q.x * k, q.y * k, q.z))
    body = ell("dog_body", body_r, pc, (0, 0, 0.038), fab_body, P.sq, fn=pear)
    add_fur(body, fur_body, seed=11)
    neck = empty("dog_neck", pc, P.sq, (0, -0.002, 0.066))
    head = ell("dog_headm", head_r, pc, (0, -0.003, 0.026), fab_head, neck)
    add_fur(head, fur_head, seed=12)
    muz = ell("dog_muzzle", (0.0175, 0.012, 0.0125), pc, (0, -0.030, -0.009), cached("dog_muzz_fab", lambda: M.fabric("dog_muzz_fab", "#FBF4E4", "polar_fleece")), head)
    add_fur(muz, fur_muzz, length=0.003, seed=13)
    nose = ell("dog_nose", (0.0062, 0.0042, 0.0046), pc, (0, -0.0125, 0.004), M.plain("dog_nose", "#3a221a", rough=0.75, sheen=0.5, noise_bump=0.5, noise_scale=1500), muz)
    tm = thread_mat("#5a3524")
    # mouth: a short stitched Y under the nose
    new_obj("dog_mouth", tube_mesh("m", [on_ell((0.0175, 0.012, 0.0125), (0, -1, 0.1), 0.0022), on_ell((0.0175, 0.012, 0.0125), (0, -1, -0.45), 0.0022)], 0.0006, tm, sides=6), pc, muz)
    for sx in (-1, 1):
        new_obj("dog_mouth%d" % sx, tube_mesh("m", [on_ell((0.0175, 0.012, 0.0125), (0, -1, -0.45), 0.0022), on_ell((0.0175, 0.012, 0.0125), (sx * 0.22, -1, -0.62), 0.0022), on_ell((0.0175, 0.012, 0.0125), (sx * 0.42, -1, -0.55), 0.0022)], 0.0006, tm, sides=6), pc, muz)
    # eyes: a bead and a bigger old button (on the rust patch)
    eL = bead("dog_eyeL", 0.0046, pc, head, on_ell(head_r, (-0.44, -0.88, 0.17), 0.0015))
    eR = button("dog_eyeR", 0.0068, pc, head, on_ell(head_r, (0.44, -0.88, 0.17), 0.0042), col="#231712")
    eR.rotation_euler = Euler((math.radians(90), 0, math.radians(24)))
    # stitched ring around the eye patch
    cen = Vector((0.017, -0.030, 0.006))
    def ring(u):
        a = u * 2 * math.pi
        d = (cen + Vector((math.cos(a) * 0.0165, 0, math.sin(a) * 0.0165)))
        return on_ell(head_r, (d.x, -abs(d.y) - 0.02, d.z), 0.0042)
    stitches("dog_patch_st", ring, pc, head, thread_mat("#e9dcc3"), n=48, dash=0.003, gap=0.0024)
    # centre seam over the head
    stitches("dog_seam", lambda u: on_ell(head_r, (0, -math.cos(lerp(0.75, 2.6, u)), math.sin(lerp(0.75, 2.6, u))), 0.0042), pc, head, thread_mat("#cdbb9c"), n=40)
    # ears: origin at the hinge, hanging down. The left (rust) one has come loose and hangs lower.
    def ear(name, sx, length, fab, furm, seed):
        hinge = empty(name + "_h", pc, head, (sx * 0.0395, 0.001, 0.016))
        hinge.rotation_euler.y = -sx * math.radians(10)
        def shape(q, p):
            w = 1 - 0.35 * max(0.0, p.z)              # narrower at the hinge
            return Vector((q.x * w, q.y, q.z - length))
        e = ell(name, (0.0145, 0.0068, length), pc, (0, 0, 0), fab, hinge, fn=shape)
        add_fur(e, furm, length=0.0035, seed=seed)
        return hinge
    P.p["earL"] = ear("dog_earL", -1, 0.0275, fab_rust, fur_rust, 14)
    P.p["earR"] = ear("dog_earR", 1, 0.0235, cached("dog_body_fab2", lambda: fab_body), fur_body, 15)
    P.p["earL"].location.z -= 0.004
    # loose thread at the left ear hinge
    lt = [Vector((0, 0, 0)) + Vector((math.sin(i * 0.9) * 0.0035 - 0.004, -0.006 - 0.0006 * i, 0.004 - i * 0.0022 + math.cos(i * 1.3) * 0.0015)) for i in range(9)]
    new_obj("dog_loose", tube_mesh("lt", lt, 0.00045, thread_mat("#8a4a2a"), sides=5), pc, P.p["earL"])
    # legs
    paw_fab = cached("dog_muzz_fab", lambda: None)
    for i, (x, y, z, rr) in enumerate(((-0.019, -0.031, 0.011, (0.0115, 0.014, 0.011)), (0.019, -0.031, 0.011, (0.0115, 0.014, 0.011)),
                                       (-0.035, -0.014, 0.011, (0.014, 0.019, 0.0115)), (0.035, -0.014, 0.011, (0.014, 0.019, 0.0115)))):
        lg = ell("dog_leg%d" % i, rr, pc, (x, y, z), fab_body, P.sq)
        lg.rotation_euler.z = math.radians(-18 if x < 0 else 18) * (1 if i > 1 else 0.3)
        add_fur(lg, fur_body, length=0.0035, seed=20 + i)
        P.p["leg%d" % i] = lg
    tail_h = empty("dog_tail_h", pc, P.sq, (0, 0.034, 0.022))
    tail = ell("dog_tail", (0.007, 0.007, 0.013), pc, (0, 0.002, 0.009), fab_rust, tail_h)
    tail_h.rotation_euler.x = math.radians(-35)
    add_fur(tail, fur_rust, length=0.0035, seed=30)
    # collar: red felt band with a brass button
    red = M.plain("dog_collar", "#B8352C", rough=0.95, sheen=0.8, noise_bump=0.8, noise_scale=1200)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, segments=40, radius1=0.0305, radius2=0.0285, depth=0.0085, cap_ends=False)
    col_o = new_obj("dog_collar", finish(bm, "dog_collar", red), pc, P.sq, (0, -0.001, 0.0655))
    col_o.scale = (1.0, 0.93, 1.0)
    col_o.modifiers.new("s", "SOLIDIFY").thickness = 0.0016
    fuzz(col_o, M.fur("dog_collar_fz", "#B8352C"), seed=31)
    button("dog_tag", 0.0052, pc, P.sq, (0.004, -0.0295, 0.064), col="#C9A24A", thread_col="#7a2a22")
    P.p.update(neck=neck, head=head, tail=tail_h, body=body)
    P.rest = {"earL": 0.0, "earR": 0.0}
    return P

# ================================================================ Clawd, the plush version
ORANGE = "#DD775B"
def build_clawd(c, name="clawd"):
    P = Plush(name, c); pc = P.c
    P.h, P.grab, P.rad = 0.088, 0.062, 0.040
    fab = cached("clawd_fab", lambda: M.fabric("clawd_fab", ORANGE, "wool_boucle", scale=9, bump=0.5, tex_amt=0.25))
    fz = cached("clawd_fz", lambda: M.fur("clawd_fz", ORANGE, vary=0.12))
    W, D, H = 0.085, 0.050, 0.065
    legh = 0.022
    def soft_box(nm, size, loc, bevel, parent, seed, pillow=0.06):
        me = box_mesh(nm, size, [fab], bevel=bevel, seg_n=4)
        o = new_obj(nm, me, pc, parent, loc)
        sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
        bpy.context.view_layer.objects.active = o
        fuzz(o, fz, seed=seed)
        return o
    body = soft_box(name + "_body", (W, D, H), (0, 0, legh + H / 2 - 0.002), 0.009, P.sq, 41)
    for i, sx in enumerate((-1, 1)):
        a = soft_box(name + "_arm%d" % i, (0.022, 0.030, 0.023), (sx * (W / 2 + 0.008), 0, legh + H * 0.55), 0.005, P.sq, 42 + i)
        P.p["arm%d" % i] = a
    for i, x in enumerate((-0.034, -0.019, 0.019, 0.034)):
        soft_box(name + "_leg%d" % i, (0.0115, 0.030, legh + 0.006), (x, 0, legh / 2 + 0.001), 0.003, P.sq, 44 + i)
    black = cached("clawd_eye", lambda: M.plain("clawd_eye", "#141110", rough=0.95, sheen=0.6, noise_bump=0.8, noise_scale=1500))
    for i, sx in enumerate((-1, 1)):
        e = box(name + "_eye%d" % i, (0.0115, 0.0022, 0.0115), pc, (sx * 0.021, -D / 2 - 0.0002, legh + H * 0.74), black, bevel=0.0008, parent=P.sq)
    # blanket stitch round the front face: ticks that wrap over the edge
    tm = thread_mat("#F3D9B8")
    bm = bmesh.new()
    y0 = -D / 2
    z0, z1 = legh + 0.004, legh + H - 0.006
    x0, x1 = -W / 2 + 0.004, W / 2 - 0.004
    def tick(p_in, p_edge, p_side):
        me = tube_mesh("t", [p_in, p_edge, p_side], 0.0006, None, sides=5)
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    n = 12
    for i in range(n + 1):
        x = lerp(x0 + 0.004, x1 - 0.004, i / n)
        tick((x, y0 - 0.0012, z1 - 0.0045), (x, y0 - 0.001, z1 + 0.0008), (x, y0 + 0.005, z1 + 0.0035))
    for i in range(8):
        z = lerp(z0 + 0.004, z1 - 0.006, i / 7)
        for sx in (-1, 1):
            xe = x1 if sx > 0 else x0
            tick((xe - sx * 0.0045, y0 - 0.0012, z), (xe + sx * 0.0008, y0 - 0.001, z), (xe + sx * 0.0036, y0 + 0.005, z))
    me = bpy.data.meshes.new(name + "_stitch"); bm.to_mesh(me); bm.free(); me.materials.append(tm)
    for p in me.polygons: p.use_smooth = True
    new_obj(name + "_stitch", me, pc, P.sq)
    def rim(u):
        per = [(x0, z0), (x0, z1 - 0.004), (x0 + 0.004, z1), (x1 - 0.004, z1), (x1, z1 - 0.004), (x1, z0)]
        k = u * (len(per) - 1); i = min(int(k), len(per) - 2); f = k - i
        return (lerp(per[i][0], per[i + 1][0], f), y0 - 0.0014, lerp(per[i][1], per[i + 1][1], f))
    stitches(name + "_rim", rim, pc, P.sq, tm, n=80, dash=0.0042, gap=0.0018, r=0.00055)
    P.p["body"] = body
    return P

# ================================================================ supporting cast
def _eyes(P, parent, pts, r=0.0038):
    for i, p in enumerate(pts): bead(P.name + "_eye%d" % i, r, P.c, parent, p)

def build_frog(c, name="frog", col="#9DB38A", belly="#F1EAD6"):
    P = Plush(name, c); pc = P.c
    P.h, P.grab, P.rad = 0.078, 0.045, 0.043
    rr = (0.044, 0.039, 0.033)
    pat = [((0, -0.034, -0.012), 0.027, belly, 0.10, (1, 1, 1.25))]
    fab = M.fabric(name + "_fab", col, "terry_cloth", scale=8, patches=pat)
    body = ell(name + "_body", rr, pc, (0, 0, 0.032), fab, P.sq)
    add_fur(body, M.fur(name + "_fur", col, patches=pat), length=0.003, seed=51, children=18)
    for i, sx in enumerate((-1, 1)):
        bump = ell(name + "_eb%d" % i, (0.0135, 0.0125, 0.0135), pc, (sx * 0.021, -0.006, 0.060), M.fabric(name + "_fab2", col, "terry_cloth", scale=8), P.sq)
        add_fur(bump, M.fur(name + "_fur2", col), length=0.003, seed=52 + i, children=18)
        bead(name + "_eye%d" % i, 0.0042, pc, bump, on_ell((0.0135, 0.0125, 0.0135), (sx * 0.15, -1, 0.1), 0.001))
        foot = ell(name + "_ft%d" % i, (0.015, 0.016, 0.008), pc, (sx * 0.031, -0.026, 0.006), M.fabric(name + "_fab2", col, "terry_cloth", scale=8), P.sq)
        add_fur(foot, M.fur(name + "_fur2", col), length=0.003, seed=54 + i, children=18)
        ck = ell(name + "_ck%d" % i, (0.0055, 0.002, 0.004), pc, on_ell(rr, (sx * 0.62, -0.75, 0.22), 0.003), cheek_mat(), body)
        ck.rotation_euler.z = sx * math.radians(38)
    # mouth: one long stitched smile
    stitches(name + "_mouth", lambda u: on_ell(rr, (lerp(-0.42, 0.42, u), -1, 0.16 - 0.10 * math.sin(u * math.pi)), 0.0032), pc, body, thread_mat("#4c5a3c"), n=30, dash=0.003, gap=0.002)
    # gingham patch on the belly, stitched on
    gm = cached("gingham", lambda: M.fabric("gingham", "#ffffff", "gingham_check", scale=22, keep_tex_colour=True, tex_amt=1.0, sheen=0.2))
    patch = box(name + "_patch", (0.018, 0.0016, 0.016), pc, on_ell(rr, (0.36, -1, -0.42), 0.0026), gm, bevel=0.0006, parent=body, rot=(-22, 0, 8))
    def pr(u):
        k = u * 4; i = int(k) % 4; f = k - int(k)
        cs = [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)]
        x = lerp(cs[i][0], cs[i + 1][0], f) * 0.0075; z = lerp(cs[i][1], cs[i + 1][1], f) * 0.0065
        return (x, -0.0013, z)
    stitches(name + "_pst", pr, pc, patch, thread_mat("#C24A3A"), n=40, dash=0.0022, gap=0.0016, r=0.00045)
    P.p["body"] = body
    return P

def build_star(c, name="star", col="#E2B341", patch_col="#D9826B"):
    P = Plush(name, c); pc = P.c
    P.h, P.grab, P.rad = 0.105, 0.055, 0.040
    R, TH = 0.054, 0.024
    def star(q, p):
        a = math.atan2(p.z, p.x)
        rxy = math.hypot(p.x, p.z)
        s = 0.76 + 0.24 * math.cos(5 * (a - math.pi / 2))          # five soft points, one up
        s = lerp(1.0, s, min(1.0, rxy * 1.4))
        edge = (1 - rxy ** 4)
        return Vector((p.x * R * s, p.y * TH * (0.55 + 0.45 * edge), p.z * R * s))
    fab = M.fabric(name + "_fab", col, "velour_velvet", scale=9, patches=[((0.030, 0, -0.034), 0.019, patch_col, 0.06)])
    body = new_obj(name + "_body", sphere_mesh(name + "_body", lambda p: star(p, p), fab, u=80, v=40), pc, P.sq, (0, 0, 0.052))
    add_fur(body, M.fur(name + "_fur", col, patches=[((0.030, 0, -0.034), 0.019, patch_col, 0.06)]), length=0.0022, seed=61, children=16, density=300000)
    def on(x, z, lift=0.0030):
        rxy = math.hypot(x, z) / R
        return (x, -TH * (0.55 + 0.45 * (1 - min(1, rxy) ** 4)) * math.sqrt(max(0.0, 1 - min(1, rxy) ** 2)) - lift - 0.002, z)
    tm = thread_mat("#5a3d1e")
    for sx in (-1, 1):       # sleepy eyes: two stitched arcs
        stitches(name + "_eye%d" % sx, lambda u, sx=sx: on(sx * 0.014 + lerp(-0.0065, 0.0065, u), 0.006 - 0.004 * math.sin(u * math.pi)), pc, body, tm, n=14, dash=0.0024, gap=0.0012, r=0.0006)
    stitches(name + "_mouth", lambda u: on(lerp(-0.004, 0.004, u), -0.007 - 0.002 * math.sin(u * math.pi)), pc, body, tm, n=8, dash=0.002, gap=0.001, r=0.0005)
    # stitched edge of the patch on the lower right point
    for i, sx in enumerate((-1, 1)):
        ck = ell(name + "_ck%d" % i, (0.0045, 0.0015, 0.003), pc, on(sx * 0.023, 0.0, 0.0005), cheek_mat(), body)
    P.p["body"] = body
    return P

def build_octo(c, name="octo", col="#B7A3D4"):
    P = Plush(name, c); pc = P.c
    P.h, P.grab, P.rad = 0.092, 0.060, 0.041
    rr = (0.041, 0.039, 0.040)
    fab = M.fabric(name + "_fab", col, "curly_teddy_natural", scale=7)
    fr = M.fur(name + "_fur", col)
    head = ell(name + "_head", rr, pc, (0, 0, 0.052), fab, P.sq)
    add_fur(head, fr, length=0.0048, seed=71, children=20, kink=(0.0006, 6))
    for i in range(7):
        a = i / 7 * 2 * math.pi + 0.2
        lg = ell(name + "_leg%d" % i, (0.012, 0.012, 0.014), pc, (math.cos(a) * 0.030, math.sin(a) * 0.028, 0.012), fab, P.sq)
        lg.rotation_euler = Euler((math.sin(a) * 0.5, -math.cos(a) * 0.5, 0))
        add_fur(lg, fr, length=0.004, seed=72 + i, children=14)
    # wonky eyes: a small bead, and a big button sewn a little too low
    bead(name + "_eye0", 0.0042, pc, head, on_ell(rr, (-0.36, -0.9, 0.05), 0.0035))
    b = button(name + "_eye1", 0.0082, pc, head, on_ell(rr, (0.42, -0.86, -0.08), 0.005), col="#F0E7D2", thread_col="#3a2a44")
    b.rotation_euler = Euler((math.radians(96), 0, math.radians(26)))
    stitches(name + "_mouth", lambda u: on_ell(rr, (lerp(-0.10, 0.12, u), -1, -0.27 - 0.05 * math.sin(u * math.pi)), 0.005), pc, head, thread_mat("#4a3760"), n=10, dash=0.0024, gap=0.0014)
    P.p["body"] = head
    return P

def build_mush(c, name="mush", cap="#B6513B", dots="#F3E9D4"):
    P = Plush(name, c); pc = P.c
    P.h, P.grab, P.rad = 0.098, 0.075, 0.046
    stem_r = (0.024, 0.023, 0.030)
    stem = ell(name + "_stem", stem_r, pc, (0, 0, 0.029), M.fabric(name + "_stem", "#F1E6CF", "polar_fleece"), P.sq, fn=lambda q, p: Vector((q.x * (1 + 0.18 * -p.z), q.y * (1 + 0.18 * -p.z), q.z)))
    add_fur(stem, M.fur(name + "_sfur", "#F1E6CF"), length=0.003, seed=81, children=16)
    CR, CH = 0.052, 0.040
    def capf(p):
        if p.z >= 0: return Vector((p.x * CR, p.y * CR * 0.94, p.z * CH))
        return Vector((p.x * CR * (1 + 0.06 * p.z), p.y * CR * 0.94 * (1 + 0.06 * p.z), p.z * 0.009))
    # dots are painted into the cloth, then stitched round
    dpos = [(0.0, -0.75, 0.62), (-0.62, -0.55, 0.45), (0.60, -0.58, 0.40), (-0.25, -0.2, 0.93), (0.35, 0.1, 0.9), (-0.8, 0.2, 0.5), (0.8, 0.3, 0.5), (0, 0.8, 0.55)]
    def cap_pt(d, lift=0.0):
        d = Vector(d).normalized(); return on_ell((CR, CR * 0.94, CH), d, lift)
    pat = [(tuple(cap_pt(d)), 0.0085 if i % 2 else 0.011, dots, 0.05) for i, d in enumerate(dpos)]
    fab = M.fabric(name + "_cap", cap, "ribbed_corduroy", scale=11, patches=pat, bump=1.0, sheen=0.8, tex_amt=0.7)
    capo = new_obj(name + "_capm", sphere_mesh(name + "_cap", capf, fab, u=48, v=28), pc, P.sq, (0, 0, 0.056))
    fuzz(capo, M.fur(name + "_cfz", cap, patches=pat), seed=82, density=120000)
    for i, d in enumerate(dpos[:3]):
        cen = cap_pt(d); rad = 0.0085 if i % 2 else 0.011
        t1 = Vector(d).normalized().cross(Vector((0, 0, 1))).normalized(); t2 = Vector(d).normalized().cross(t1)
        stitches(name + "_ds%d" % i, lambda u, cen=cen, t1=t1, t2=t2, rad=rad: cap_pt(cen + (t1 * math.cos(u * 6.283) + t2 * math.sin(u * 6.283)) * rad, 0.0012), pc, capo, thread_mat("#8E3524"), n=30, dash=0.0022, gap=0.0018, r=0.00045)
    _eyes(P, stem, [on_ell(stem_r, (-0.42, -1, 0.1), 0.002), on_ell(stem_r, (0.42, -1, 0.1), 0.002)], 0.0034)
    for i, sx in enumerate((-1, 1)):
        ell(name + "_ck%d" % i, (0.004, 0.0015, 0.0028), pc, on_ell(stem_r, (sx * 0.7, -0.8, -0.12), 0.0024), cheek_mat(), stem)
    P.p["body"] = capo
    return P

def build_cloud(c, name="cloud", col="#9FB6CB"):
    P = Plush(name, c); pc = P.c
    P.h, P.grab, P.rad = 0.078, 0.050, 0.046
    fab = M.fabric(name + "_fab", col, "wool_boucle", scale=8, bump=0.9)
    fr = M.fur(name + "_fur", col)
    main = None
    for i, (x, z, r) in enumerate(((-0.030, 0.034, 0.028), (0.002, 0.044, 0.035), (0.033, 0.032, 0.026), (-0.006, 0.026, 0.026), (0.018, 0.026, 0.024))):
        o = ell(name + "_b%d" % i, (r, r * 0.85, r), pc, (x, 0.004 if i > 2 else 0, z), fab, P.sq)
        add_fur(o, fr, length=0.0042, seed=91 + i, children=16, kink=(0.0005, 8))
        if i == 1: main = o
    _eyes(P, main, [on_ell((0.035, 0.03, 0.035), (-0.3, -1, -0.12), 0.0035), on_ell((0.035, 0.03, 0.035), (0.3, -1, -0.12), 0.0035)], 0.0042)
    drop_m = cached("drop", lambda: M.plain("drop", "#6FA8D8", rough=0.08, coat=1.0))
    tm = thread_mat("#F3EFE6")
    for i, x in enumerate((-0.022, 0.004, 0.027)):
        new_obj(name + "_dt%d" % i, tube_mesh("t", [(x, -0.012, 0.010), (x, -0.013, 0.002 - (i % 2) * 0.002)], 0.00045, tm, sides=5), pc, P.sq)
        ell(name + "_drop%d" % i, (0.0042, 0.0042, 0.0058), pc, (x, -0.013, -0.002 - (i % 2) * 0.002), drop_m, P.sq, u=20, v=14, fn=lambda q, p: Vector((q.x * (1 - 0.45 * max(0, p.z)), q.y * (1 - 0.45 * max(0, p.z)), q.z)))
    P.p["body"] = main
    return P

KINDS = {"dog": build_dog, "clawd": build_clawd, "frog": build_frog, "star": build_star, "octo": build_octo, "mush": build_mush, "cloud": build_cloud}
