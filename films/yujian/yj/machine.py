"""The claw machine as a small stage, the shop outside the glass, and the person (a coat and a mitten)."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Euler
from .common import *
from . import mats as M
from .plush import add_fur, fuzz, stitches, thread_mat, button, cached

CHUTE = Vector(((HOLE[0] + HOLE[1]) / 2, (HOLE[2] + HOLE[3]) / 2, 0.0))   # centre of the hole
HAND_UV = (0.90, 0.17)                                     # the hand print on the front glass (u, v from bottom-left)
HAND_POS = Vector((X0 + (X1 - X0) * HAND_UV[0], Y0, -0.02 + (ZT + 0.01) * HAND_UV[1]))

def glass_mat(name, tex, dirt=1.0, mirror=0.28):
    """Thin glass: see-through, a fresnel reflection, and smudges that catch the light."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
    out = M.out_of(m)
    uv = M.node(nt, "ShaderNodeTexCoord")
    im = M.node(nt, "ShaderNodeTexImage"); im.image = M.image(os.path.join(TEX, tex), "Non-Color"); im.extension = "EXTEND"
    nt.links.new(uv.outputs["UV"], im.inputs["Vector"])
    sm = M.math_n(nt, "MULTIPLY", im.outputs["Color"], dirt)
    tr = M.node(nt, "ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.93, 0.97, 0.96, 1)
    gl = M.node(nt, "ShaderNodeBsdfGlossy")
    nt.links.new(M.math_n(nt, "ADD", M.math_n(nt, "MULTIPLY", sm, 0.45), 0.015), gl.inputs["Roughness"])
    fr = M.node(nt, "ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
    mix1 = M.node(nt, "ShaderNodeMixShader")
    nt.links.new(M.math_n(nt, "MINIMUM", M.math_n(nt, "ADD", M.math_n(nt, "MULTIPLY", fr.outputs[0], 1.1), 0.02), mirror), mix1.inputs[0])   # capped: at grazing angles it must not turn into a mirror
    nt.links.new(tr.outputs[0], mix1.inputs[1]); nt.links.new(gl.outputs[0], mix1.inputs[2])
    df = M.node(nt, "ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (0.85, 0.86, 0.84, 1)
    tl = M.node(nt, "ShaderNodeBsdfTranslucent"); tl.inputs["Color"].default_value = (0.85, 0.86, 0.84, 1)
    haze = M.node(nt, "ShaderNodeAddShader"); nt.links.new(df.outputs[0], haze.inputs[0]); nt.links.new(tl.outputs[0], haze.inputs[1])
    mix2 = M.node(nt, "ShaderNodeMixShader")
    nt.links.new(M.math_n(nt, "MULTIPLY", sm, 0.30, clamp=True), mix2.inputs[0])
    nt.links.new(mix1.outputs[0], mix2.inputs[1]); nt.links.new(haze.outputs[0], mix2.inputs[2])
    nt.links.new(mix2.outputs[0], out.inputs["Surface"])
    M.MATS[name] = m
    return m

def pane(name, c, p0, p1, p2, p3, m):
    """Quad with UVs 0..1 (p0 bottom-left, p1 bottom-right, p2 top-right, p3 top-left as seen from outside)."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in (p0, p1, p2, p3)]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new("UVMap")
    for loop, co in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): loop[uv].uv = co
    o = new_obj(name, finish(bm, name, m, smooth=False), c)
    o.visible_shadow = False
    return o

def enamel(name, col, tex="blue_metal_plate", scale=3.0, wear=0.5):
    """Old painted sheet metal: our colour, the texture's scratches and dents."""
    m, nt, b = M._new(name)
    vec, tc = M.obj_coords(nt, scale)
    d = M.box_tex(nt, M.ph(tex, "diff"), vec)
    bw = M.node(nt, "ShaderNodeRGBToBW"); nt.links.new(d, bw.inputs[0])
    lum = M.math_n(nt, "ADD", M.math_n(nt, "MULTIPLY", M.math_n(nt, "SUBTRACT", bw.outputs[0], 0.35), 1.6 * wear), 1.0)
    nt.links.new(M.mix_n(nt, 1.0, lin(col), lum, "MULTIPLY"), b.inputs["Base Color"])
    r = M.box_tex(nt, M.ph(tex, "rough"), vec, "Non-Color")
    rb = M.node(nt, "ShaderNodeRGBToBW"); nt.links.new(r, rb.inputs[0])
    nt.links.new(M.math_n(nt, "ADD", M.math_n(nt, "MULTIPLY", rb.outputs[0], 0.5), 0.18), b.inputs["Roughness"])
    nm = M.node(nt, "ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.6
    nt.links.new(M.box_tex(nt, M.ph(tex, "nor"), vec, "Non-Color"), nm.inputs["Color"]); nt.links.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = 0.25
    return m

def stripes_mat(name, a, b_, width=0.03):
    m, nt, b = M._new(name)
    tc = M.node(nt, "ShaderNodeTexCoord")
    sx = M.node(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    f = M.math_n(nt, "GREATER_THAN", M.math_n(nt, "FRACT", M.math_n(nt, "DIVIDE", sx.outputs[0], width * 2)), 0.5)
    vec, _ = M.obj_coords(nt, 14)
    d = M.box_tex(nt, M.ph("cotton_jersey", "diff"), vec)
    bw = M.node(nt, "ShaderNodeRGBToBW"); nt.links.new(d, bw.inputs[0])
    lum = M.math_n(nt, "ADD", M.math_n(nt, "MULTIPLY", M.math_n(nt, "SUBTRACT", bw.outputs[0], 0.5), 1.2), 1.0)
    nt.links.new(M.mix_n(nt, 1.0, M.mix_n(nt, f, lin(a), lin(b_)), lum, "MULTIPLY"), b.inputs["Base Color"])
    nm = M.node(nt, "ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
    nt.links.new(M.box_tex(nt, M.ph("cotton_jersey", "nor"), vec, "Non-Color"), nm.inputs["Color"]); nt.links.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.9; b.inputs["Sheen Weight"].default_value = 0.5
    return m

POM_COLS = ["#E9B7A6", "#F2DDA4", "#B9D3C2", "#C9B8DA", "#F3EBDD", "#E58E73", "#A9C4D9", "#F0C96A"]

def build_bed(c):
    """The filler: a bed of small felt pompoms, one mesh, coloured per ball through a colour attribute."""
    rnd = random.Random(5)
    bm = bmesh.new()
    cl = bm.loops.layers.color.new("Col")
    balls = []
    def add(x, y, z, r):
        col = lin(rnd.choice(POM_COLS))
        k = 0.85 + 0.3 * rnd.random()
        col = (col[0] * k, col[1] * k, col[2] * k, 1)
        ret = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=__import__("mathutils").Matrix.Translation((x, y, z)))
        fs = set()
        for v in ret["verts"]:
            for f in v.link_faces: fs.add(f)
        for f in fs:
            for l in f.loops: l[cl] = col
        balls.append((x, y, z, r))
    def in_hole(x, y, m=0.012):
        return HOLE[0] - m < x < HOLE[1] + m and HOLE[2] - m < y < HOLE[3] + m
    step = 0.0195
    for layer in range(2):
        yy = Y0 + 0.012
        row = 0
        while yy < Y1 - 0.008:
            xx = X0 + 0.012 + (step / 2 if row % 2 else 0) + layer * step * 0.5
            while xx < X1 - 0.008:
                x = xx + rnd.uniform(-0.004, 0.004); y = yy + rnd.uniform(-0.004, 0.004) + layer * step * 0.3
                r = rnd.uniform(0.0085, 0.0125)
                if not in_hole(x, y) and (layer == 0 or rnd.random() < 0.45):
                    add(x, y, -0.021 + layer * 0.013 + rnd.uniform(-0.003, 0.003), r)
                xx += step
            yy += step * 0.87; row += 1
    fab = M.fabric("pom_fab", "#ffffff", None, bump=0.8)
    nt = fab.node_tree; b = M.bsdf_of(fab)
    at = M.node(nt, "ShaderNodeVertexColor"); at.layer_name = "Col"
    nt.links.new(at.outputs["Color"], b.inputs["Base Color"])
    furm = M.fur("pom_fur", "#ffffff", vary=0.2)
    nt2 = furm.node_tree
    hsv = next(n for n in nt2.nodes if n.type == "HUE_SAT")
    at2 = M.node(nt2, "ShaderNodeVertexColor"); at2.layer_name = "Col"
    nt2.links.new(at2.outputs["Color"], hsv.inputs["Color"])
    me = finish(bm, "bed", fab)
    o = new_obj("bed", me, c)
    add_fur(o, furm, length=0.0022, density=110000, children=8, seed=3, rand=1.0)
    return o

def star_mesh(name, R, r, th, m):
    bm = bmesh.new()
    vs = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = R if i % 2 == 0 else r
        vs.append(bm.verts.new((math.cos(a) * rr, 0, math.sin(a) * rr)))
    f = bm.faces.new(vs)
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]: v.co.y -= th
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return finish(bm, name, m, smooth=False)

class Machine:
    pass

def build_machine(c):
    Mx = Machine()
    mc = coll("machine", c)
    mint = enamel("enamel_mint", "#8FBFAE")
    cream = enamel("enamel_cream", "#EFE3C6", wear=0.4)
    red = enamel("enamel_red", "#C4473A", wear=0.35)
    chrome = M.worn_metal("chrome", scratch=0.8, oil=0.35)
    dark = M.plain("dark_felt", "#1d1a1c", rough=0.95, sheen=0.4, noise_bump=0.6, noise_scale=900)
    # ---- bed
    Mx.bed = build_bed(mc)
    box("bed_base_a", (X1 - HOLE[1], Y1 - Y0, 0.04), mc, ((X1 + HOLE[1]) / 2, 0, -0.045), dark)
    box("bed_base_b", (HOLE[1] - X0, Y1 - HOLE[3], 0.04), mc, ((HOLE[1] + X0) / 2, (Y1 + HOLE[3]) / 2, -0.045), dark)
    # chute walls below the hole and an acrylic guard above it
    acr = glass_mat("acrylic", "glass_side.png", dirt=0.6)
    gh = 0.062
    pane("guard_x", mc, (HOLE[1], HOLE[2], -0.02), (HOLE[1], HOLE[3], -0.02), (HOLE[1], HOLE[3], gh), (HOLE[1], HOLE[2], gh), acr)
    pane("guard_y", mc, (HOLE[0], HOLE[3], -0.02), (HOLE[1], HOLE[3], -0.02), (HOLE[1], HOLE[3], gh), (HOLE[0], HOLE[3], gh), acr)
    for i, (p, q) in enumerate((((HOLE[1], HOLE[2], gh), (HOLE[1], HOLE[3], gh)), ((HOLE[0], HOLE[3], gh), (HOLE[1], HOLE[3], gh)), ((HOLE[1], HOLE[3], -0.02), (HOLE[1], HOLE[3], gh)))):
        new_obj("guard_trim%d" % i, tube_mesh("gt", [p, q], 0.0028, red, sides=8), mc)
    box("chute_x", (0.004, HOLE[3] - HOLE[2], 0.5), mc, (HOLE[1] + 0.002, (HOLE[2] + HOLE[3]) / 2, -0.27), dark)
    box("chute_y", (HOLE[1] - HOLE[0], 0.004, 0.5), mc, ((HOLE[0] + HOLE[1]) / 2, HOLE[3] + 0.002, -0.27), dark)
    # ---- back wall: old paper-coloured felt with faded felt stars and a paper moon
    wall = box("back_wall", (X1 - X0 + 0.06, 0.02, ZT + 0.12), mc, (0, Y1 + 0.01, ZT / 2 - 0.03), M.fabric("wall_felt", "#E6D3AE", "cotton_jersey", scale=6, bump=0.9, tex_amt=0.6))
    fuzz(wall, M.fur("wall_fz", "#E6D3AE"), density=40000, seed=7)
    rnd = random.Random(11)
    star_cols = ["#D9A441", "#C9655A", "#7FA9A0", "#EFE6D0", "#B58DB6"]
    for i in range(13):
        x = rnd.uniform(X0 + 0.04, X1 - 0.04); z = rnd.uniform(0.10, ZT - 0.09)
        R = rnd.uniform(0.014, 0.034)
        col = star_cols[i % len(star_cols)]
        sm = cached("starfelt" + col, lambda col=col: M.fabric("starfelt" + col, col, None, bump=1.2))
        s = new_obj("wstar%d" % i, star_mesh("wstar", R, R * 0.48, 0.0022, sm), mc, None, (x, Y1 - 0.0005, z))
        s.rotation_euler.y = rnd.uniform(-0.5, 0.5)
        stitches("wstar_st%d" % i, lambda u, R=R: (lambda a, rr: (math.cos(a) * rr, -0.003, math.sin(a) * rr))(math.pi / 2 + u * 2 * math.pi, R * 0.78 * (1 - 0.42 * abs(math.sin(u * 5 * math.pi)))), mc, s, thread_mat("#F6EEDC" if i % 2 else "#6b4a2e"), n=60, dash=0.003, gap=0.0025, r=0.0005)
    moon = cyl("wmoon", 0.05, 0.05, 0.0025, mc, (0.13, Y1 - 0.0015, 0.33), M.fabric("moonfelt", "#F1DFA0", None, bump=1.2), rot=(90, 0, 0), seg_n=48)
    stitches("wmoon_st", lambda u: (math.cos(u * 6.283) * 0.044, math.sin(u * 6.283) * 0.044, 0.0018), mc, moon, thread_mat("#B9893A"), n=80, dash=0.004, gap=0.003, r=0.0006)
    # ---- side and front glass
    Mx.glass_front_mat = glass_mat("glass_front", "glass_front.png")
    gs = glass_mat("glass_side", "glass_side.png", dirt=0.45, mirror=0.045)
    Mx.glass_front = pane("glass_front", mc, (X0, Y0, -0.02), (X1, Y0, -0.02), (X1, Y0, ZT - 0.01), (X0, Y0, ZT - 0.01), Mx.glass_front_mat)
    pane("glass_left", mc, (X0, Y1, -0.02), (X0, Y0, -0.02), (X0, Y0, ZT), (X0, Y1, ZT), gs)
    pane("glass_right", mc, (X1, Y0, -0.02), (X1, Y1, -0.02), (X1, Y1, ZT), (X1, Y0, ZT), gs)
    # ---- frame: corner posts, sill, header
    for i, (x, y) in enumerate(((X0 - 0.015, Y0 - 0.015), (X1 + 0.015, Y0 - 0.015), (X0 - 0.015, Y1 + 0.015), (X1 + 0.015, Y1 + 0.015))):
        box("post%d" % i, (0.03, 0.03, ZT + 0.06), mc, (x, y, ZT / 2 - 0.01), mint, bevel=0.004)
    box("sill_front", (X1 - X0 + 0.06, 0.03, 0.03), mc, (0, Y0 - 0.015, -0.035), mint, bevel=0.004)
    box("sill_l", (0.03, Y1 - Y0, 0.03), mc, (X0 - 0.015, 0, -0.035), mint, bevel=0.004)
    box("sill_r", (0.03, Y1 - Y0, 0.03), mc, (X1 + 0.015, 0, -0.035), mint, bevel=0.004)
    box("ceiling", (X1 - X0 + 0.06, Y1 - Y0 + 0.06, 0.02), mc, (0, 0, ZT + 0.01), cream)
    box("header", (X1 - X0 + 0.08, 0.05, 0.14), mc, (0, Y0 - 0.02, ZT + 0.09), red, bevel=0.006)
    box("header_l", (0.05, Y1 - Y0 + 0.05, 0.14), mc, (X0 - 0.02, 0.02, ZT + 0.09), red, bevel=0.006)
    box("header_r", (0.05, Y1 - Y0 + 0.05, 0.14), mc, (X1 + 0.02, 0.02, ZT + 0.09), red, bevel=0.006)
    # ---- valance: scalloped striped cloth along the inside top of the front and back
    def valance(name, y, depth_dir):
        bm = bmesh.new()
        nx = 121; drop = 0.058
        rows = 6
        grid = []
        for j in range(rows + 1):
            row = []
            for i in range(nx):
                u = i / (nx - 1); x = lerp(X0, X1, u)
                sc = abs(math.sin(u * math.pi * 8))                 # eight scallops
                bottom = drop * (0.55 + 0.45 * sc)
                z = ZT - 0.004 - bottom * j / rows
                wave = 0.004 * math.sin(u * math.pi * 16 + 1.0) * (j / rows) ** 1.5
                row.append(bm.verts.new((x, y + depth_dir * wave, z)))
            grid.append(row)
        for j in range(rows):
            for i in range(nx - 1):
                bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
        o = new_obj(name, finish(bm, name, stripes_mat("valance", "#C4473A", "#F1E4C8", 0.0375)), mc)
        o.modifiers.new("s", "SOLIDIFY").thickness = 0.0012
        return o
    valance("valance_front", Y0 + 0.012, 1)
    valance("valance_back", Y1 - 0.006, -1)
    # ---- bulbs: a row along the front top (behind the valance) and one along the back
    Mx.bulbs = []
    socket = M.plain("socket", "#3a2f28", rough=0.5, metal=0.6)
    wire = M.plain("wire", "#1c1715", rough=0.5)
    nb = 9
    for row, (y, z) in enumerate(((Y0 + 0.030, ZT - 0.070), (Y1 - 0.022, ZT - 0.072))):
        pts = []
        for i in range(nb):
            x = lerp(X0 + 0.04, X1 - 0.04, i / (nb - 1))
            zz = z - 0.004 * math.sin(i / (nb - 1) * math.pi * (nb - 1)) ** 2
            bm_ = M.plain("bulb%d_%d" % (row, i), "#FFE9C4", rough=0.25, emit="#FFC98A", es=6.0)
            b = ell("bulb%d_%d" % (row, i), (0.0095, 0.0095, 0.0115), mc, (x, y, zz - 0.012), bm_, u=20, v=14)
            b.visible_shadow = False
            cyl("sock%d_%d" % (row, i), 0.005, 0.0055, 0.008, mc, (x, y, zz + 0.002), socket, seg_n=12)
            Mx.bulbs.append(bm_)
            pts.append((x, y, zz + 0.006))
        fine = []
        for (a, b2) in zip(pts, pts[1:]):
            for k in range(8):
                u = k / 8; p = Vector(a).lerp(Vector(b2), u); p.z -= 0.008 * math.sin(u * math.pi); fine.append(p)
        fine.append(Vector(pts[-1]))
        new_obj("bulbwire%d" % row, tube_mesh("bw", fine, 0.0011, wire, sides=5), mc)
    # ---- lights that do the real work
    def area(name, loc, target, size, energy, col, sy=None):
        L = bpy.data.lights.new(name, "AREA"); L.size = size; L.energy = energy; L.color = col
        if sy: L.shape = "RECTANGLE"; L.size_y = sy
        o = new_obj(name, L, mc); look_at(o, loc, target); return L
    Mx.key = area("key_top", (0.02, -0.06, ZT - 0.012), (0.02, -0.02, 0), 0.30, 3.6, (1.0, 0.80, 0.56), sy=0.22)
    Mx.front_row = area("row_front", (0, Y0 + 0.03, ZT - 0.09), (0, 0.05, 0.02), 0.42, 2.2, (1.0, 0.78, 0.52), sy=0.02)
    Mx.back_row = area("row_back", (0, Y1 - 0.03, ZT - 0.09), (0, -0.05, 0.05), 0.42, 0.5, (1.0, 0.76, 0.50), sy=0.02)
    Mx.fill = area("front_fill", (0.0, Y0 - 0.30, 0.44), (0.0, -0.04, 0.07), 0.5, 3.2, (1.0, 0.90, 0.78), sy=0.25)
    Mx.last_lamp = bpy.data.lights.new("last_lamp", "SPOT"); Mx.last_lamp.energy = 0.0; Mx.last_lamp.color = (1.0, 0.80, 0.55)
    Mx.last_lamp.spot_size = math.radians(70); Mx.last_lamp.spot_blend = 0.6; Mx.last_lamp.shadow_soft_size = 0.02
    # the machine's own light falling out through the front glass onto whoever is standing there
    Mx.spill = bpy.data.lights.new("spill", "SPOT"); Mx.spill.energy = 0.0; Mx.spill.color = (1.0, 0.82, 0.60)
    Mx.spill.spot_size = math.radians(42); Mx.spill.spot_blend = 0.8; Mx.spill.shadow_soft_size = 0.03
    Mx.spill_o = new_obj("spill", Mx.spill, mc)
    ll = new_obj("last_lamp", Mx.last_lamp, mc); look_at(ll, (0.06, -0.02, ZT - 0.07), (-0.02, -0.12, 0.12))        # on the claw and the patch of glass where they said goodbye
    # ---- cabinet below the glass: control shelf, coin slot, prize door
    cab_front = box("cab_front", (X1 - X0 + 0.06, 0.03, 0.62), mc, (0, Y0 - 0.015, -0.36), mint, bevel=0.004)
    box("cab_l", (0.03, Y1 - Y0 + 0.03, 0.62), mc, (X0 - 0.015, 0.015, -0.36), mint)
    box("cab_r", (0.03, Y1 - Y0 + 0.03, 0.62), mc, (X1 + 0.015, 0.015, -0.36), mint)
    shelf = box("shelf", (X1 - X0 + 0.07, 0.13, 0.03), mc, (0, Y0 - 0.085, -0.075), cream, bevel=0.008)
    shelf.rotation_euler.x = math.radians(-12)
    box("shelf_trim", (X1 - X0 + 0.074, 0.012, 0.036), mc, (0, Y0 - 0.150, -0.089), red, bevel=0.004)
    # joystick and button
    cyl("joy_base", 0.022, 0.026, 0.008, mc, (0.10, Y0 - 0.085, -0.056), chrome, rot=(-12, 0, 0))
    cyl("joy_stick", 0.004, 0.004, 0.05, mc, (0.10, Y0 - 0.092, -0.030), chrome, rot=(-18, 6, 0), seg_n=12)
    ell("joy_ball", (0.014, 0.014, 0.014), mc, (0.103, Y0 - 0.100, -0.003), M.plain("joy_ball", "#C4473A", rough=0.15, coat=1.0), u=24, v=16)
    cyl("btn_ring", 0.019, 0.019, 0.006, mc, (0.19, Y0 - 0.085, -0.056), chrome, rot=(-12, 0, 0))
    Mx.btn_mat = M.plain("btn_cap", "#F2C14E", rough=0.2, coat=1.0, emit="#F2C14E", es=0.6)
    cyl("btn_cap", 0.015, 0.014, 0.008, mc, (0.19, Y0 - 0.086, -0.050), Mx.btn_mat, rot=(-12, 0, 0))
    # coin slot plate on the front panel
    cy = Y0 - 0.031
    Mx.coin_pos = Vector((0.12, cy, -0.185))
    box("coin_plate", (0.07, 0.004, 0.11), mc, (0.12, cy, -0.20), chrome, bevel=0.0015)
    box("coin_slot", (0.004, 0.006, 0.034), mc, (0.12, cy - 0.001, -0.185), M.plain("slot_dark", "#050404", rough=0.9))
    Mx.coin_lamp = M.plain("coin_lamp", "#FFB060", rough=0.3, emit="#FF9A40", es=1.5)
    box("coin_lamp", (0.03, 0.004, 0.012), mc, (0.12, cy - 0.001, -0.232), Mx.coin_lamp, bevel=0.0015)
    for i, (dx, dz) in enumerate(((-0.029, 0.048), (0.029, 0.048), (-0.029, -0.048), (0.029, -0.048))):
        cyl("coin_screw%d" % i, 0.003, 0.003, 0.003, mc, (0.12 + dx, cy - 0.002, -0.20 + dz), chrome, rot=(90, 0, 0), seg_n=8)
    Mx.coin_light = area("coin_light", (-0.10, Y0 - 0.45, -0.02), (0.12, cy, -0.19), 0.25, 0.0, (0.75, 0.85, 1.0))
    # prize door: an opening in the front panel onto the foot of the chute shaft. The flap is hinged at the sill and
    # falls open outward like a drawbridge, to rest on the tray's edge. (The dog is as tall as the opening: a flap
    # hinged at the top would have to stand on its head.)
    Mx.door_c = Vector((CHUTE.x, Y0 - 0.031, -0.40))
    dw, dh = 0.14, 0.13                                 # the shaft behind is 0.145 wide
    cut = box("door_cut", (dw, 0.08, dh), mc, (CHUTE.x, Y0 - 0.015, -0.40))
    cut.hide_render = True; cut.display_type = "WIRE"
    bo = cab_front.modifiers.new("door", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = cut
    box("door_frame_t", (dw + 0.03, 0.008, 0.015), mc, (CHUTE.x, Y0 - 0.032, -0.40 + dh / 2 + 0.0075), chrome, bevel=0.002)
    box("door_frame_b", (dw + 0.03, 0.008, 0.015), mc, (CHUTE.x, Y0 - 0.032, -0.40 - dh / 2 - 0.0075), chrome, bevel=0.002)
    box("door_frame_l", (0.015, 0.008, dh), mc, (CHUTE.x - dw / 2 - 0.0075, Y0 - 0.032, -0.40), chrome, bevel=0.002)
    box("door_frame_r", (0.015, 0.008, dh), mc, (CHUTE.x + dw / 2 + 0.0075, Y0 - 0.032, -0.40), chrome, bevel=0.002)
    Mx.door_w, Mx.door_h = dw, dh
    Mx.bin_floor_z = -0.40 - dh / 2 - 0.020             # the bin is a little deeper than the sill, so a plush sitting in it clears the lintel
    box("bin_floor", (HOLE[1] - HOLE[0], HOLE[3] - Y0 + 0.03, 0.004), mc, (CHUTE.x, (Y0 - 0.03 + HOLE[3]) / 2, Mx.bin_floor_z - 0.002), dark)
    box("bin_wall_l", (0.002, HOLE[3] - Y0, 0.19), mc, (HOLE[0] + 0.001, (Y0 + HOLE[3]) / 2, -0.39), dark)      # the cabinet side is mint: line it where the door shows it
    Mx.bin_lamp = area("bin_lamp", (CHUTE.x, Y0 + 0.010, -0.40 + dh / 2 + 0.017), (CHUTE.x, Y0 + 0.045, -0.44), 0.05, 0.0, (1.0, 0.80, 0.58))   # lit only in the door shot
    Mx.flap = empty("flap_hinge", mc, None, (CHUTE.x, Y0 - 0.037, -0.40 - dh / 2 + 0.002))
    Mx.flap_len = dh - 0.004
    Mx.flap_obj = box("flap", (dw - 0.004, 0.003, Mx.flap_len), mc, (0, 0, 0), M.plain("flap", "#7a2f28", rough=0.08, coat=1.0), bevel=0.001, parent=Mx.flap, origin=(0, 0, -1))
    Mx.tray_top = -0.40 - dh / 2 - 0.006
    box("door_tray", (dw + 0.03, 0.06, 0.012), mc, (CHUTE.x, Y0 - 0.06, -0.40 - dh / 2 - 0.012), cream, bevel=0.004)
    return Mx

# ================================================================ the shop outside
class Shop: pass
def build_shop(c):
    S = Shop()
    sc = coll("shop", c)
    S.lights = []
    rnd = random.Random(3)
    cols = ["#47C8D8", "#4F7BFF", "#E85FA8", "#7EE0C0", "#FFB45A", "#9A7BFF", "#FFFFFF"]
    S.mats = []
    def emis(name, col, es):
        m = M.plain(name, "#000000", rough=1.0, emit=col, es=es); m["base_es"] = es; S.mats.append(m); return m
    # points of light across the shop: signs, screens, other machines
    for i in range(46):
        col = cols[rnd.randrange(len(cols))]
        m = emis("neon%d" % i, col, rnd.uniform(4, 16))
        x = rnd.uniform(-2.6, 2.6); y = rnd.uniform(-5.5, -2.2); z = rnd.uniform(-0.2, 1.5)
        if rnd.random() < 0.3:
            o = box("neon%d" % i, (rnd.uniform(0.08, 0.3), 0.01, rnd.uniform(0.02, 0.06)), sc, (x, y, z), m)
        else:
            o = ell("neon%d" % i, (0.03, 0.03, 0.03), sc, (x, y, z), m, u=12, v=8)
        o.visible_shadow = False
    # far lights on the back wall: they turn into soft discs behind the cabinet
    for i in range(44):
        col = cols[rnd.randrange(len(cols) - 1)]
        x = rnd.uniform(-2.9, 2.9); z = rnd.uniform(-0.35, 1.5)
        if abs(x) < 0.38: x += math.copysign(0.5, x)
        o = ell("far%d" % i, (0.011, 0.011, 0.011), sc, (x, 3.2 - rnd.uniform(0, 0.8), z), emis("far%d" % i, col, rnd.uniform(20, 70)), u=10, v=6)
        o.visible_shadow = False
    # the machines either side of ours: only their glow and outline, at the edges of the wide shots
    for i, (x, body, glow) in enumerate(((-0.78, "#B8607A", "#FFB8A0"), (0.78, "#5E86A8", "#BFE6FF"))):
        nb = empty("side_machine%d" % i, sc, None, (x, 0.50, 0))
        nb.rotation_euler.z = math.radians(-8 if x < 0 else 8)
        bm_ = enamel("side_enamel%d" % i, body)
        for j, (px, py) in enumerate(((-0.26, -0.21), (0.26, -0.21), (-0.26, 0.21), (0.26, 0.21))):
            box("side_post%d_%d" % (i, j), (0.03, 0.03, 0.56), sc, (px, py, 0.24), bm_, parent=nb)
        box("side_base%d" % i, (0.56, 0.46, 0.66), sc, (0, 0, -0.38), bm_, parent=nb)
        box("side_head%d" % i, (0.58, 0.48, 0.14), sc, (0, 0, 0.56), bm_, parent=nb)
        g = emis("side_glow%d" % i, glow, 0.10)
        box("side_back%d" % i, (0.50, 0.01, 0.50), sc, (0, 0.20, 0.23), g, parent=nb)
        for j in range(9):
            col = cols[rnd.randrange(len(cols) - 1)]
            ell("side_toy%d_%d" % (i, j), (0.04, 0.04, 0.045), sc, (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.15, 0.15), 0.035), M.plain("side_toy%d_%d" % (i, j), col, rough=0.9, sheen=0.6), nb, u=14, v=10)
        L = bpy.data.lights.new("side_lamp%d" % i, "POINT"); L.energy = 0.22; L.color = lin(glow)[:3]; L.shadow_soft_size = 0.05; L["base"] = 0.22
        new_obj("side_lamp%d" % i, L, sc, nb, (0, 0, 0.40)); S.lights.append(L)
    # neighbouring machines seen through the side glass
    for i, (x, col, y) in enumerate(((-1.6, "#E85FA8", 0.3), (1.9, "#47C8D8", 0.2), (-2.6, "#FFB45A", -0.6), (2.9, "#9A7BFF", -0.5))):
        box("nb_body%d" % i, (0.7, 0.6, 1.9), sc, (x, y, 0.1), M.plain("nb_body%d" % i, "#15171d", rough=0.5))
        m = emis("nb_win%d" % i, col, 0.10)
        w = box("nb_win%d" % i, (0.56, 0.02, 0.5), sc, (x, y - 0.31, 0.3), m)
        w2 = box("nb_side%d" % i, (0.02, 0.5, 0.5), sc, (x - math.copysign(0.36, x), y, 0.3), m)
    # neon on the far wall, either side of the machine (seen soft, behind the cabinet)
    for i, (x, z, w, h, col, es) in enumerate(((-0.72, 0.52, 0.012, 0.42, "#47C8D8", 9), (-0.60, 0.20, 0.20, 0.012, "#4F7BFF", 7), (-0.95, 0.05, 0.012, 0.5, "#E85FA8", 6),
                                              (0.70, 0.45, 0.012, 0.55, "#9A7BFF", 8), (0.92, 0.30, 0.22, 0.012, "#47C8D8", 7), (0.62, -0.05, 0.16, 0.012, "#E85FA8", 5),
                                              (-0.50, -0.25, 0.3, 0.012, "#7EE0C0", 4), (1.15, -0.10, 0.012, 0.6, "#4F7BFF", 6))):
        o = box("wallneon%d" % i, (w * 2.2, 0.012, h * 2.2), sc, (x * 2.4, 3.3, z * 2.2 + 0.2), emis("wallneon%d" % i, col, es * 1.6), bevel=0.004)
        o.visible_shadow = False
    box("shop_floor", (9, 9, 0.02), sc, (0, -2, -0.72), M.plain("shop_floor", "#1b1d24", rough=0.25))
    box("shop_wall", (12, 0.05, 6), sc, (0, 3.4, 0.8), M.plain("shop_wall", "#1a1c26", rough=0.9))
    box("shop_back", (9, 0.05, 4), sc, (0, -6.2, 0.8), M.plain("shop_back", "#10121a", rough=0.9))
    def area(name, loc, target, size, energy, col):
        L = bpy.data.lights.new(name, "AREA"); L.size = size; L.energy = energy; L.color = col; L["base"] = energy
        o = new_obj(name, L, sc); look_at(o, loc, target); return L
    S.cool = area("shop_cool", (-0.9, -1.6, 1.3), (0, -0.2, 0.2), 1.2, 14, (0.45, 0.70, 1.0))
    S.cool2 = area("shop_cool2", (1.2, -1.0, 0.9), (0.1, -0.1, 0.2), 0.8, 8, (0.85, 0.45, 0.9))
    S.morning = area("shop_morning", (-2.2, -2.0, 1.2), (0, -0.2, 0.25), 1.6, 0.0, (1.0, 0.72, 0.52))
    S.window = emis("shop_window", "#FFC9A0", 0.0)
    box("shop_window", (2.4, 0.02, 1.6), sc, (-1.4, -6.0, 0.9), S.window)
    w = bpy.data.worlds.new("world"); bpy.context.scene.world = w; w.use_nodes = True
    S.world = w.node_tree.nodes["Background"]
    S.world.inputs[0].default_value = (0.012, 0.016, 0.03, 1)
    return S

def set_shop(S, level=1.0, morning=0.0):
    """level: neon and cool light 0..1. morning: 0..1 warm daylight through the shop window."""
    for m in S.mats:
        if m is S.window: continue
        M.set_emit(m, m["base_es"] * level)
    S.cool.energy = S.cool["base"] * (0.12 + 0.88 * level) * (1 - 0.7 * morning)
    for L in S.lights: L.energy = L["base"] * level
    S.cool2.energy = S.cool2["base"] * level
    S.morning.energy = 60 * morning
    M.set_emit(S.window, 9 * morning)
    k = morning
    S.world.inputs[0].default_value = (lerp(0.012, 0.16, k), lerp(0.016, 0.11, k), lerp(0.03, 0.09, k), 1)

# ================================================================ the person: a coat and a mitten
class Person: pass
def build_person(c):
    P = Person()
    pc = coll("person", c)
    P.c = pc
    P.root = empty("person", pc)
    coat = M.fabric("coat", "#27324A", "knitted_fleece", scale=5, bump=1.0)
    torso = ell("coat", (0.21, 0.13, 0.42), pc, (0, 0, 0.12), coat, P.root, fn=lambda q, p: Vector((q.x * (1 - 0.25 * max(0, p.z)), q.y, q.z)))
    scarf = ell("scarf", (0.11, 0.10, 0.045), pc, (0, 0, 0.50), M.fabric("scarf", "#D9A441", "knitted_fleece", scale=9, bump=1.2), P.root)
    # mitten hand, origin at the palm centre; the palm faces +Y (toward the glass)
    P.hand = empty("hand", pc)
    mit = M.fabric("mitten", "#C9655A", "knitted_fleece", scale=12, bump=1.2)
    mf = M.fur("mitten_fz", "#C9655A")
    palm = ell("mit_palm", (0.034, 0.016, 0.046), pc, (0, 0, 0.006), mit, P.hand)
    fuzz(palm, mf, length=0.0018, density=150000, seed=5)
    th = ell("mit_thumb", (0.012, 0.011, 0.024), pc, (-0.034, 0.0, -0.012), mit, P.hand)
    th.rotation_euler.y = math.radians(28)
    fuzz(th, mf, length=0.0018, density=150000, seed=6)
    # the sleeve hangs off a wrist so the arm can come up from below while the palm stays flat on the glass
    P.wrist = empty("wrist", pc, P.hand, (0, 0, -0.036))
    cuff = cyl("mit_cuff", 0.027, 0.030, 0.035, pc, (0, 0, -0.016), M.fabric("cuff", "#F1E4C8", "knitted_fleece", scale=14, bump=1.5), P.wrist, seg_n=24)
    cuff.scale = (1, 0.62, 1)
    arm = cyl("mit_arm", 0.034, 0.040, 0.30, pc, (0, 0, -0.175), coat, P.wrist, seg_n=24)
    arm.scale = (1, 0.7, 1)
    return P
