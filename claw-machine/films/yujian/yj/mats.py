"""Materials: fabric, fur strands, thread, beads, metal, glass."""
import bpy, os, math
from .common import lin, ASSETS, TEX, tryset

MATS = {}
def bsdf_of(m): return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
def out_of(m): return next(n for n in m.node_tree.nodes if n.type == "OUTPUT_MATERIAL")

def _new(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    MATS[name] = m
    return m, m.node_tree, bsdf_of(m)

def node(nt, typ, **props):
    n = nt.nodes.new(typ)
    for k, v in props.items(): setattr(n, k, v)
    return n
def math_n(nt, op, a, b=None, clamp=False):
    n = node(nt, "ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: nt.links.new(v, n.inputs[i])
    return n.outputs[0]
def mix_n(nt, fac, a, b, blend="MIX"):
    n = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type=blend)
    for sock, v in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
        if isinstance(v, (int, float)): sock.default_value = v
        elif isinstance(v, (tuple, list)): sock.default_value = v
        else: nt.links.new(v, sock)
    return n.outputs[2]
def image(path, colorspace="sRGB"):
    key = os.path.abspath(path)
    for im in bpy.data.images:
        if im.filepath == key: return im
    im = bpy.data.images.load(key)
    im.colorspace_settings.name = colorspace
    return im
def obj_coords(nt, scale=1.0, rot=(0, 0, 0)):
    tc = node(nt, "ShaderNodeTexCoord")
    mp = node(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    mp.inputs["Rotation"].default_value = rot
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs[0], tc
def box_tex(nt, path, vec, colorspace="sRGB"):
    n = node(nt, "ShaderNodeTexImage", projection="BOX")
    n.projection_blend = 0.35
    n.image = image(path, colorspace)
    nt.links.new(vec, n.inputs["Vector"])
    return n.outputs["Color"]
def ph(asset, m): return os.path.join(ASSETS, "polyhaven", asset, m + ".jpg")

def patches_colour(nt, base, patches):
    """Base colour with round patches painted in object space: [(centre, radius, hex, softness)]."""
    tc = node(nt, "ShaderNodeTexCoord")
    col = None
    cur = lin(base)
    for (cen, rad, hx, *rest) in patches:
        soft = rest[0] if rest else 0.12
        sq = rest[1] if len(rest) > 1 else (1, 1, 1)
        mp = node(nt, "ShaderNodeMapping")
        mp.inputs["Location"].default_value = tuple(-c * s for c, s in zip(cen, sq))
        mp.inputs["Scale"].default_value = sq
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        ln = node(nt, "ShaderNodeVectorMath", operation="LENGTH")
        nt.links.new(mp.outputs[0], ln.inputs[0])
        mr = node(nt, "ShaderNodeMapRange")
        mr.inputs[1].default_value = rad * (1 - soft); mr.inputs[2].default_value = rad * (1 + soft)
        mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.0
        nt.links.new(ln.outputs["Value"], mr.inputs[0])
        col = mix_n(nt, mr.outputs[0], col if col is not None else cur, lin(hx))
    if col is None:
        rgb = node(nt, "ShaderNodeRGB"); rgb.outputs[0].default_value = cur
        col = rgb.outputs[0]
    return col

def fabric(name, col, tex="polar_fleece", scale=7.0, patches=(), bump=0.6, rough=0.95, sheen=0.6, tex_amt=0.5, keep_tex_colour=False, rot=(0, 0, 0)):
    """Cloth: recoloured Poly Haven fabric (luminance detail times our colour) with its normal map."""
    m, nt, b = _new(name)
    vec, tc = obj_coords(nt, scale, rot)
    base = patches_colour(nt, col, patches)
    if tex:
        d = box_tex(nt, ph(tex, "diff"), vec)
        if keep_tex_colour:
            colour = mix_n(nt, tex_amt, base, d, "MULTIPLY")
        else:
            bw = node(nt, "ShaderNodeRGBToBW"); nt.links.new(d, bw.inputs[0])
            # centre the luminance around 1 so the fabric keeps our colour
            lum = math_n(nt, "ADD", math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", bw.outputs[0], 0.5), 2.0 * tex_amt), 1.0)
            colour = mix_n(nt, 1.0, base, lum, "MULTIPLY")
            mm = nt.nodes[-1]
            # MULTIPLY wants a colour in B: route the scalar through
        nt.links.new(colour, b.inputs["Base Color"])
        nm = node(nt, "ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = bump
        nt.links.new(box_tex(nt, ph(tex, "nor"), vec, "Non-Color"), nm.inputs["Color"])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])
    else:
        nt.links.new(base, b.inputs["Base Color"])
        nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 4
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = node(nt, "ShaderNodeBump"); bp.inputs["Strength"].default_value = bump * 0.5; bp.inputs["Distance"].default_value = 0.0006
        nt.links.new(nz.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Sheen Roughness"].default_value = 0.5
    b.inputs["Specular IOR Level"].default_value = 0.2
    return m

def fur(name, col, patches=(), vary=0.18, rough=0.9, sheen=0.3, tip_light=0.25):
    """Strand shader for particle hair: wool-like, slightly different shade per strand, lighter at the tip."""
    m, nt, b = _new(name)
    base = patches_colour(nt, col, patches)
    hi = node(nt, "ShaderNodeHairInfo")
    # per-strand value shift
    v = math_n(nt, "ADD", math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", hi.outputs["Random"], 0.5), 2 * vary), 1.0)
    tip = math_n(nt, "ADD", math_n(nt, "MULTIPLY", hi.outputs["Intercept"], tip_light), 1.0 - tip_light * 0.5)
    hsv = node(nt, "ShaderNodeHueSaturation")
    nt.links.new(base, hsv.inputs["Color"])
    nt.links.new(math_n(nt, "MULTIPLY", v, tip), hsv.inputs["Value"])
    nt.links.new(hsv.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Specular IOR Level"].default_value = 0.15
    return m

def plain(name, col, rough=0.5, metal=0.0, emit=None, es=0.0, coat=0.0, spec=0.5, sheen=0.0, noise_bump=0.0, noise_scale=400):
    m, nt, b = _new(name)
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Sheen Weight"].default_value = sheen
    if emit:
        b.inputs["Emission Color"].default_value = lin(emit)
        b.inputs["Emission Strength"].default_value = es
    if noise_bump:
        tc = node(nt, "ShaderNodeTexCoord")
        nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise_scale; nz.inputs["Detail"].default_value = 3
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = node(nt, "ShaderNodeBump"); bp.inputs["Strength"].default_value = noise_bump; bp.inputs["Distance"].default_value = 0.0005
        nt.links.new(nz.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    return m

def thread(name, col):
    """Embroidery thread: twisted look from a diagonal wave bump."""
    m, nt, b = _new(name)
    b.inputs["Base Color"].default_value = lin(col)
    b.inputs["Roughness"].default_value = 0.7
    b.inputs["Sheen Weight"].default_value = 0.4
    tc = node(nt, "ShaderNodeTexCoord")
    wv = node(nt, "ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 2500; wv.bands_direction = "DIAGONAL"
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bp = node(nt, "ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.0003
    nt.links.new(wv.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    return m

def worn_metal(name, col="#c9c6c0", scratch=1.0, oil=0.6, tex="metal_plate", scale=30.0):
    """Old chrome: fine scratches in the roughness, dark oil in the creases and around joints."""
    m, nt, b = _new(name)
    vec, tc = obj_coords(nt, scale)
    r = box_tex(nt, ph(tex, "rough"), vec, "Non-Color")
    bw = node(nt, "ShaderNodeRGBToBW"); nt.links.new(r, bw.inputs[0])
    # long thin scratches: stretched noise
    mp = node(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (4000, 60, 4000); mp.inputs["Rotation"].default_value = (0.3, 0.2, 0.5)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = node(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    sc = node(nt, "ShaderNodeMapRange"); sc.inputs[1].default_value = 0.58; sc.inputs[2].default_value = 0.66
    nt.links.new(nz.outputs[0], sc.inputs[0])
    mp2 = node(nt, "ShaderNodeMapping"); mp2.inputs["Scale"].default_value = (80, 5000, 3000); mp2.inputs["Rotation"].default_value = (0.9, 0.1, 1.2)
    nt.links.new(tc.outputs["Object"], mp2.inputs["Vector"])
    nz2 = node(nt, "ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 1.0; nz2.inputs["Detail"].default_value = 6
    nt.links.new(mp2.outputs[0], nz2.inputs["Vector"])
    sc2 = node(nt, "ShaderNodeMapRange"); sc2.inputs[1].default_value = 0.6; sc2.inputs[2].default_value = 0.68
    nt.links.new(nz2.outputs[0], sc2.inputs[0])
    scr = math_n(nt, "MAXIMUM", sc.outputs[0], sc2.outputs[0])
    rough = math_n(nt, "ADD", math_n(nt, "MULTIPLY", bw.outputs[0], 0.10), math_n(nt, "MULTIPLY", scr, 0.10 * scratch), clamp=True)
    rough = math_n(nt, "ADD", rough, 0.13)
    # oil / grime: big soft noise + ambient occlusion
    gz = node(nt, "ShaderNodeTexNoise"); gz.inputs["Scale"].default_value = 60; gz.inputs["Detail"].default_value = 5
    nt.links.new(tc.outputs["Object"], gz.inputs["Vector"])
    gm = node(nt, "ShaderNodeMapRange"); gm.inputs[1].default_value = 0.5; gm.inputs[2].default_value = 0.72
    nt.links.new(gz.outputs[0], gm.inputs[0])
    ao = node(nt, "ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = 0.012; ao.samples = 8
    inv = math_n(nt, "SUBTRACT", 1.0, ao.outputs["AO"])
    aom = node(nt, "ShaderNodeMapRange"); aom.inputs[1].default_value = 0.15; aom.inputs[2].default_value = 0.6
    nt.links.new(inv, aom.inputs[0])
    grime = math_n(nt, "MULTIPLY", math_n(nt, "ADD", math_n(nt, "MULTIPLY", gm.outputs[0], 0.5), aom.outputs[0], clamp=True), oil)
    colr = mix_n(nt, grime, lin(col), lin("#3a2a1c"))
    colr = mix_n(nt, math_n(nt, "MULTIPLY", scr, 0.08), colr, lin("#f2f0ec"))
    nt.links.new(colr, b.inputs["Base Color"])
    nt.links.new(math_n(nt, "ADD", rough, math_n(nt, "MULTIPLY", grime, 0.25), clamp=True), b.inputs["Roughness"])
    nt.links.new(math_n(nt, "SUBTRACT", 1.0, math_n(nt, "MULTIPLY", grime, 0.6)), b.inputs["Metallic"])
    
    return m

def set_emit(m, s): bsdf_of(m).inputs["Emission Strength"].default_value = s
