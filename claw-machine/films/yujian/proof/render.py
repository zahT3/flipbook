"""Renders for the proof film. Same scene code as the film (yj/), only the materials, visibility or camera change.

  blender -b --factory-startup -P films/yujian/proof/render.py -- --mode layers --frame 505 --out <dir> [--scale 100] [--samples 48]
      clay.png (every material grey clay, fur kept), nofur.png, wire.png, explode_00..11.png (fur off, parts in colours, flying apart)
  ... --mode orbit --frame 24 --n 72 --out <dir>      time frozen at drawing 24, the camera goes once round the machine
  ... --mode sync --frames 6-39 --what clay|wire --out <dir>   a passage of the film again, every drawing, in clay or wireframe
  ... --mode build --out <dir>                        the dog put together part by part, as build_dog() does it, turning slowly
"""
import sys, os, math, time, colorsys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bpy
from mathutils import Vector, Matrix
from yj.common import *
from yj import anim as AN, plush as PL, mats as M

MODE = arg("--mode", "layers")
OUT = os.path.abspath(arg("--out", "out/proof"))
os.makedirs(OUT, exist_ok=True)
scene = init_scene(samples=int(arg("--samples", "48")), scale=int(arg("--scale", "100")))
scene.view_settings.view_transform = "Standard"
scene.cycles.transparent_max_bounces = 64
GLASS = ("glass_front", "glass_side", "acrylic")

def render(name):
    fp = os.path.join(OUT, name)
    if os.path.exists(fp) and not flag("--force"): return
    scene.render.filepath = fp
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("FRAME %s %.1fs" % (fp, time.time() - t0), flush=True)

def meshes():
    return [o for o in scene.objects if o.type in ("MESH", "CURVE") and not o.hide_render]

def fur(on):
    for o in scene.objects:
        for m in o.modifiers:
            if m.type == "PARTICLE_SYSTEM": m.show_render = on

def clay_mat(name, col, rough=0.62):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    return m

def wire_mat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = strength
    wf = nt.nodes.new("ShaderNodeWireframe"); wf.use_pixel_size = True; wf.inputs["Size"].default_value = float(arg("--wire", "1.3"))
    nt.links.new(wf.outputs[0], mix.inputs[0]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs["Surface"])
    return m

def set_all(o, m):
    if not hasattr(o.data, "materials"): return
    if len(o.data.materials) == 0: o.data.materials.append(m)
    for i in range(len(o.data.materials)): o.data.materials[i] = m

def is_glass(o):
    return any(s.material and s.material.name.startswith(GLASS) for s in o.material_slots)

def group_of(o, W):
    if o.name in W.plush["dog"].c.all_objects: return "dog"
    if o.name in W.claw.c.all_objects: return "claw"
    return "rest"

PASTEL = [colorsys.hsv_to_rgb(h, 0.42, 0.92) for h in (0.02, 0.08, 0.13, 0.30, 0.47, 0.56, 0.66, 0.78, 0.90)]

if MODE in ("layers", "orbit"):
    W = AN.build_all(scene)
    F = int(arg("--frame", "505"))
    AN.pose(W, F / 12)
    bpy.context.view_layer.update()

if MODE == "sync":
    # one passage of the film, every drawing again in clay (fur kept) or in wireframe: --frames 6-39 --what clay|wire
    W = AN.build_all(scene)
    WHAT = arg("--what", "clay")
    glass = {o.name for o in meshes() if is_glass(o)}
    if WHAT == "clay":
        clay = clay_mat("clay", (0.40, 0.40, 0.40))
        for o in meshes():
            if o.name not in glass: set_all(o, clay)
    else:
        fur(False)
        wm = {"dog": wire_mat("w_dog", (1.0, 0.55, 0.30), 1.6), "claw": wire_mat("w_claw", (0.45, 0.80, 1.0), 1.6), "rest": wire_mat("w_rest", (0.65, 0.68, 0.75), 0.45)}
        for o in scene.objects:
            if o.type in ("MESH", "CURVE"): set_all(o, wm[group_of(o, W)])
    for f in parse_frames(arg("--frames", "6-39")):
        AN.pose(W, f / 12)
        if WHAT == "wire":
            for o in scene.objects:
                if o.type == "LIGHT": o.hide_render = True
            if scene.world: scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
        render("%s_%04d.png" % (WHAT, f))

if MODE == "layers":
    glass = {o.name for o in meshes() if is_glass(o)}
    glass_keep = {o.name: o.material_slots[0].material for o in meshes() if is_glass(o)}          # decided once: later steps replace the glass's material too
    clay = clay_mat("clay", (0.40, 0.40, 0.40))
    # 1. clay: every material replaced by one grey, except the glass, so the camera still looks through it
    for o in meshes():
        if o.name not in glass: set_all(o, clay)
    render("clay.png")
    # 2. the same without the fur
    fur(False)
    render("nofur.png")
    # 3. wireframe: dog orange, claw blue, everything else dim
    wm = {"dog": wire_mat("w_dog", (1.0, 0.55, 0.30), 1.6), "claw": wire_mat("w_claw", (0.45, 0.80, 1.0), 1.6), "rest": wire_mat("w_rest", (0.65, 0.68, 0.75), 0.45)}
    for o in meshes(): set_all(o, wm[group_of(o, W)])
    world_col = scene.world.node_tree.nodes["Background"].inputs[0].default_value[:] if scene.world else None
    lamps = [(o, o.hide_render) for o in scene.objects if o.type == "LIGHT"]
    for o, _ in lamps: o.hide_render = True
    if scene.world: scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    render("wire.png")
    for o, h in lamps: o.hide_render = h
    if scene.world: scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    # 4. the dog and the claw fly apart into the shapes they are built from; each part its own colour
    parts = [o for o in meshes() if group_of(o, W) in ("dog", "claw")]
    for i, o in enumerate(sorted(parts, key=lambda o: o.name)):
        set_all(o, clay_mat("p_" + o.name, PASTEL[i % len(PASTEL)], 0.5))
    for o in meshes():
        if o not in parts: set_all(o, glass_keep[o.name] if o.name in glass else clay)
    bpy.context.view_layer.update()
    dogc = W.plush["dog"].root.matrix_world.translation + Vector((0, 0, 0.065))
    hubc = W.claw.hub.matrix_world.translation.copy()
    home = {}
    for o in parts:
        mw = o.matrix_world.copy()
        c = sum((mw @ Vector(b) for b in o.bound_box), Vector()) / 8
        cen = dogc if group_of(o, W) == "dog" else hubc
        d = c - cen
        home[o.name] = (mw, d + (d.normalized() * 0.012 if d.length > 1e-4 else Vector((0, 0, 0.012))))
    for o in parts:
        o.parent = None
        o.matrix_world = home[o.name][0]
    N = int(arg("--n", "12"))
    amt = float(arg("--amount", "1.1"))
    for k in range(N):
        p = k / (N - 1)
        e = amt * (1 - (1 - p) ** 3)
        for o in parts:
            mw, d = home[o.name]
            o.matrix_world = Matrix.Translation(d * e) @ mw
        render("explode_%02d.png" % k)

if MODE == "orbit":
    # time stands still at drawing F; clear away the shop furniture the camera would pass through
    for o in list(bpy.data.collections["shop"].all_objects):
        if o.name == "shop_floor" or o.name.startswith(("shop_cool", "shop_morning", "shop_wall", "shop_back")): continue
        p = o.matrix_world.translation
        if o.name.startswith(("side_", "nb_")) or math.hypot(p.x, p.y) < 3.0: o.hide_render = True
    cam = W.cam
    cam.data.dof.use_dof = False
    cam.data.lens = float(arg("--lens", "35"))
    R, Z = float(arg("--radius", "2.3")), float(arg("--height", "0.18"))
    tgt = Vector((0, 0, float(arg("--tz", "-0.06"))))
    N = int(arg("--n", "72"))
    for k in range(N):
        a = -math.pi / 2 + 2 * math.pi * k / N
        look_at(cam, (R * math.cos(a), R * math.sin(a), Z), tgt)
        render("orbit_%03d.png" % k)

if MODE == "build":
    # the dog alone on a felt ground, put together in the order build_dog() makes it
    st = coll("stage")
    box("ground", (3, 3, 0.02), st, (0, 0, -0.01), M.fabric("ground", "#D9C4A0", "cotton_jersey", scale=5, bump=0.8))
    P = PL.build_dog(st)
    def area(name, loc, target, size, energy, col):
        L = bpy.data.lights.new(name, "AREA"); L.size = size; L.energy = energy; L.color = col
        o = new_obj(name, L, st); look_at(o, loc, target)
    area("key", (-0.35, -0.45, 0.5), (0, 0, 0.06), 0.35, 7, (1.0, 0.86, 0.68))
    area("fill", (0.5, -0.3, 0.2), (0, 0, 0.06), 0.5, 1.5, (0.6, 0.75, 1.0))
    area("rim", (0.2, 0.5, 0.35), (0, 0, 0.08), 0.3, 5, (1.0, 0.9, 0.8))
    w = bpy.data.worlds.new("w"); scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.045, 0.06, 1)
    cam = new_obj("cam", bpy.data.cameras.new("cam"), st); scene.camera = cam
    cam.data.lens = 85; cam.data.clip_start = 0.01
    look_at(cam, (0.0, -0.92, 0.17), (0, 0, 0.068))
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = 0.90; cam.data.dof.aperture_fstop = 5.6
    STEPS = [("dog_body",), ("dog_headm",), ("dog_muzzle", "dog_nose", "dog_mouth"), ("dog_eyeL", "dog_eyeR"),
             ("dog_patch_st", "dog_seam"), ("dog_earL", "dog_earR", "dog_loose"), ("dog_leg",), ("dog_tail", "dog_collar", "dog_tag")]
    objs = [o for o in P.c.all_objects if o.type in ("MESH", "CURVE")]
    step_of = {}
    for o in objs:
        step_of[o.name] = next((i for i, pre in enumerate(STEPS) if o.name.startswith(pre)), 0)
    lens0 = {}
    for o in objs:
        for m in o.modifiers:
            if m.type == "PARTICLE_SYSTEM": lens0[(o.name, m.name)] = m.particle_system.settings.hair_length
    PER = int(arg("--per", "16"))                    # drawings per step; the fur step is twice as long
    FUR = len(STEPS)
    total = PER * len(STEPS) + PER * 2
    base_scale = {o.name: o.scale.copy() for o in objs}
    P.root.rotation_euler.z = 0
    for k in range(total):
        step, sub = (k // PER, k % PER) if k < PER * len(STEPS) else (FUR, k - PER * len(STEPS))
        P.root.rotation_euler.z = math.radians(-38 + 70 * k / total)
        for o in objs:
            s = step_of[o.name]
            vis = s <= step
            o.hide_render = not vis
            pop = 1.0
            if s == step and step < FUR: pop = back(min(1.0, (sub + 1) / 4.0)) if sub < 4 else 1.0
            o.scale = base_scale[o.name] * max(0.02, pop)
        g = 0.0 if step < FUR else ss(min(1.0, (sub + 1) / (PER * 1.2)))
        for o in objs:
            for m in o.modifiers:
                if m.type == "PARTICLE_SYSTEM":
                    m.show_render = g > 0.0
                    if g > 0: m.particle_system.settings.hair_length = max(1e-4, lens0[(o.name, m.name)] * g)
        print("STEP", k, step, flush=True)
        render("build_%03d.png" % k)
print("TOTAL_DONE", flush=True)
