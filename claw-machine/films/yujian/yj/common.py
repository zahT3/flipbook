"""Shared helpers: args, easing, scene setup, mesh builders."""
import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Euler, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(HERE, "assets")
TEX = os.path.join(HERE, "tex")

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
def flag(name): return name in argv
def parse_frames(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b != a else float(t >= b)
def ss(p): p = clamp(p); return p * p * (3 - 2 * p)
def eo(p): p = clamp(p); return 1 - (1 - p) ** 3
def ei(p): p = clamp(p); return p ** 3
def back(p, s=1.9): p = clamp(p) - 1; return 1 + p * p * ((s + 1) * p + s)
def lerp(a, b, p): return a + (b - a) * p
def vlerp(a, b, p): return Vector(a).lerp(Vector(b), p)
def hsh(*k):
    random.seed(repr(k)); return random.random()
def spring(t, t0, freq=3.0, damp=4.0):
    """Damped wobble starting at t0: 1 at t0, rings down to 0."""
    if t < t0: return 0.0
    d = t - t0
    return math.exp(-damp * d) * math.cos(2 * math.pi * freq * d)
def kf(t, keys, ease=ss):
    """Keyframes [(time, value), ...]; values are floats or tuples."""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            p = ease(seg(t, t0, t1))
            if isinstance(v0, (int, float)): return lerp(v0, v1, p)
            return tuple(lerp(a, b, p) for a, b in zip(v0, v1))
    return keys[-1][1]

def lin(hx, a=1.0):
    hx = hx.lstrip("#")
    c = [int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (a,)

def tryset(o, k, v):
    try: setattr(o, k, v)
    except Exception as e: print("skip", k, e)

# ---------------------------------------------------------------- scene
def init_scene(samples=64, scale=100, engine="CYCLES"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = engine
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, scale
    r.fps = 24
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.use_persistent_data = True
    cy = scene.cycles
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    tryset(cy, "denoiser", "OPENIMAGEDENOISE")
    tryset(cy, "denoising_input_passes", "RGB_ALBEDO_NORMAL")
    cy.max_bounces = 6
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 4
    cy.transmission_bounces = 6
    cy.transparent_max_bounces = 12
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.sample_clamp_indirect = 6.0
    tryset(scene.cycles_curves, "shape", "RIBBONS")
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices: d.use = True
        cy.device = "GPU"
    except Exception as e:
        print("GPU setup failed:", e)
    return scene

COLLS = {}
def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    COLLS[name] = c
    return c
def show(name, on):
    c = COLLS[name]
    c.hide_render = not on
    c.hide_viewport = not on

def new_obj(name, data, c, parent=None, loc=(0, 0, 0), rot=None):
    o = bpy.data.objects.new(name, data)
    c.objects.link(o)
    if parent: o.parent = parent
    o.location = loc
    if rot: o.rotation_euler = Euler([math.radians(a) for a in rot])
    return o
def empty(name, c, parent=None, loc=(0, 0, 0)):
    return new_obj(name, None, c, parent, loc)

def finish(bm, name, m=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if m is not None:
        for mm in (m if isinstance(m, (list, tuple)) else [m]): me.materials.append(mm)
    return me

def box_mesh(name, size, m=None, bevel=0.0, origin=(0, 0, 0), seg_n=3, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] - origin[0] * size[0] / 2,
                       v.co.y * size[1] - origin[1] * size[1] / 2,
                       v.co.z * size[2] - origin[2] * size[2] / 2))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=seg_n, affect="EDGES", profile=0.5)
    return finish(bm, name, m, smooth)
def box(name, size, c, loc=(0, 0, 0), m=None, bevel=0.0, parent=None, origin=(0, 0, 0), rot=None, seg_n=3):
    o = new_obj(name, box_mesh(name, size, m, bevel, origin, seg_n), c, parent, loc, rot)
    if bevel > 0: add_autosmooth(o)
    return o
def add_autosmooth(o, angle=40):
    try:
        for p in o.data.polygons: p.use_smooth = True
        o.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception as e: pass

def cyl(name, r1, r2, h, c, loc=(0, 0, 0), m=None, parent=None, rot=None, seg_n=32, caps=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg_n, radius1=r1, radius2=r2, depth=h)
    o = new_obj(name, finish(bm, name, m), c, parent, loc, rot)
    add_autosmooth(o)
    return o

def sphere_mesh(name, fn=None, m=None, u=40, v=24):
    """UV sphere of radius 1 pushed through fn(Vector) -> Vector."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    if fn:
        for vt in bm.verts: vt.co = Vector(fn(vt.co.copy()))
    return finish(bm, name, m)
def ell(name, radii, c, loc=(0, 0, 0), m=None, parent=None, rot=None, u=40, v=24, fn=None):
    rx, ry, rz = radii
    def f(p):
        q = Vector((p.x * rx, p.y * ry, p.z * rz))
        return fn(q, p) if fn else q
    return new_obj(name, sphere_mesh(name, f, m, u, v), c, parent, loc, rot)

def tube_mesh(name, pts, rad, m=None, sides=8, cap=True, axis=None):
    """A tube along a polyline. rad is a float or a list per point."""
    bm = bmesh.new()
    rings = []
    n = len(pts)
    up = Vector((0, 0, 1))
    for i, p in enumerate(pts):
        p = Vector(p)
        d = (Vector(pts[min(i + 1, n - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        a = Vector(axis) if axis else d.cross(up)       # a fixed axis keeps a flat bar from twisting
        if a.length < 1e-4: a = d.cross(Vector((1, 0, 0)))
        a.normalize(); b = d.cross(a).normalized()
        rr = rad[i] if isinstance(rad, (list, tuple)) else rad
        rings.append([bm.verts.new(p + (a * math.cos(k * 2 * math.pi / sides) + b * math.sin(k * 2 * math.pi / sides)) * rr) for k in range(sides)])
        up = b.cross(d) if abs(b.cross(d).length) > 1e-4 else up
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(sides):
            bm.faces.new((r0[k], r0[(k + 1) % sides], r1[(k + 1) % sides], r1[k]))
    if cap:
        bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    return finish(bm, name, m)

def look_at(o, pos, target, roll=0.0):
    o.location = pos
    d = Vector(target) - Vector(pos)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if roll: o.rotation_euler.rotate_axis("Z", roll)

# ---------------------------------------------------------------- machine dimensions (interior; bed top at z = 0)
X0, X1, Y0, Y1, ZT = -0.25, 0.25, -0.20, 0.20, 0.47       # front glass at Y0
HOLE = (-0.25, -0.105, -0.20, -0.055)                      # x0, x1, y0, y1 of the prize hole (front left)
