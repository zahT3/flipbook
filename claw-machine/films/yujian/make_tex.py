"""Procedural textures for the glass: dust, wipe streaks, fingerprints and the one hand print.
  python3 films/yujian/make_tex.py   -> films/yujian/tex/glass_front.png (smudge mask, white = dirty)
The front pane is 0.50 m wide and 0.48 m tall; the texture maps 1:1 onto it.
"""
import numpy as np, os
from PIL import Image, ImageFilter, ImageDraw
rng = np.random.default_rng(7)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex"); os.makedirs(OUT, exist_ok=True)
W, H = 2400, 2200                      # 4 px per mm

def blur(a, r): return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
def noise(scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((H // scale + 2, W // scale + 2)).astype(np.float32)
    return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255

def fingerprint(size=90, seed=0):
    """An oval pad of ridges: a loop pattern, broken and uneven like a real greasy print."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[-1:1:size * 1j, -1:1:size * 1j]
    cx, cy = r.uniform(-0.3, 0.3), r.uniform(0.2, 0.7)
    d = np.hypot((xx - cx) * r.uniform(0.7, 1.0), (yy - cy) * r.uniform(1.3, 1.9))       # stretched arches, not rings
    warp = 0.9 * np.sin(xx * r.uniform(2, 4) + r.uniform(0, 6)) + 0.6 * np.sin(yy * r.uniform(3, 5) + r.uniform(0, 6))
    ridges = 0.5 + 0.5 * np.sin(d * r.uniform(20, 26) + warp)
    pad = np.clip(1 - (xx ** 2 / 0.55 + yy ** 2 / 0.85), 0, 1) ** 0.5
    lo = r.random((size // 8 + 1, size // 8 + 1)).astype(np.float32)
    blot = np.asarray(Image.fromarray((lo * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC), np.float32) / 255
    out = (0.35 + 0.65 * ridges) * pad * (0.25 + 0.75 * blot)
    return np.asarray(Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9)), np.float32) / 255

def stamp(dst, src, x, y, k=1.0):
    h, w = src.shape
    x0, y0 = int(x - w / 2), int(y - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    dst[ya:yb, xa:xb] = np.maximum(dst[ya:yb, xa:xb], src[ya - y0:yb - y0, xa - x0:xb - x0] * k)

def rot(a, deg): return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).rotate(deg, expand=True, resample=Image.BICUBIC), np.float32) / 255

def mitten(scale=1.0, seed=1):
    """A print left by a mitten: the rim of the palm and the thumb show, the middle is patchy."""
    s = int(380 * scale)
    def shape(grow=0):
        im = Image.new("L", (s, s), 0); d = ImageDraw.Draw(im)
        g = grow
        d.ellipse((s * 0.34 - g, s * 0.08 - g, s * 0.80 + g, s * 0.80 + g), fill=255)             # palm and fingers, one piece
        d.ellipse((s * 0.10 - g, s * 0.40 - g, s * 0.34 + g, s * 0.60 + g), fill=255)             # thumb, standing clear
        d.polygon([(s * 0.26, s * 0.52), (s * 0.40, s * 0.50), (s * 0.44, s * 0.68), (s * 0.30, s * 0.62)], fill=255)
        return np.asarray(im.filter(ImageFilter.GaussianBlur(s * 0.012)), np.float32) / 255
    a = shape(0)
    inner = np.asarray(Image.fromarray((shape(0) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(s * 0.05)), np.float32) / 255
    rim = np.clip(a - inner * 0.85, 0, 1) * 2.2
    r = np.random.default_rng(seed)
    tex = np.asarray(Image.fromarray((r.random((s // 10, s // 10)) * 255).astype(np.uint8)).resize((s, s), Image.BICUBIC), np.float32) / 255
    knit = 0.5 + 0.5 * np.sin(np.mgrid[0:s, 0:s][0] * 0.9) * np.sin(np.mgrid[0:s, 0:s][1] * 0.9)   # the wool leaves a weave
    return np.clip(a * (0.10 + 0.30 * tex * knit) + rim * (0.5 + 0.5 * tex), 0, 1)

def build(seed, hand_at=None, hand_strength=1.0):
    r = np.random.default_rng(seed)
    m = np.zeros((H, W), np.float32)
    # dust: fine speckle, heavier toward the bottom and the corners
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    grad = np.clip((yy / H) ** 2.2 * 0.5 + (np.abs(xx / W - 0.5) * 2) ** 4 * 0.35 + ((1 - yy / H) ** 6) * 0.3, 0, 1)
    speck = (r.random((H, W)) > 0.985).astype(np.float32)
    m += blur(speck, 1.2) * 1.6 * (0.12 + grad)
    m += noise(260, seed + 1) * noise(40, seed + 2) * 0.14 * (0.15 + grad)
    # wipe streaks: someone cleaned it with a cloth in arcs
    st = np.zeros((H, W), np.float32)
    for i in range(7):
        cx, cy, rad = r.uniform(-0.2, 1.2) * W, r.uniform(0.8, 1.9) * H, r.uniform(0.6, 1.4) * H
        d = np.abs(np.hypot(xx - cx, yy - cy) - rad)
        band = np.clip(1 - d / r.uniform(60, 160), 0, 1)
        fine = 0.6 + 0.4 * noise(90, seed + 30 + i)
        st += band * fine * r.uniform(0.05, 0.14)
    m += st
    # fingerprints: clusters at child height and near the middle
    fp = np.zeros((H, W), np.float32)
    for i in range(38):
        cx, cy = r.normal(0.5, 0.26) * W, r.normal(0.62, 0.18) * H
        for j in range(r.integers(1, 5)):
            f = rot(fingerprint(int(r.uniform(56, 84)), seed * 100 + i * 7 + j), r.uniform(-50, 50))
            stamp(fp, f, cx + j * r.uniform(52, 70), cy + r.uniform(-25, 25), r.uniform(0.25, 0.7))
    # smears: a print dragged sideways
    for i in range(9):
        cx, cy = r.uniform(0.1, 0.9) * W, r.uniform(0.3, 0.9) * H
        sm = np.zeros((H, W), np.float32)
        ln = r.uniform(120, 420)
        for k in range(0, int(ln), 6):
            stamp(sm, fingerprint(60, i) * 0.5, cx + k, cy + np.sin(k / 60) * 14, 0.4 * (1 - k / ln))
        fp = np.maximum(fp, blur(sm, 5) * 1.6)
    m += fp * 0.36
    hand = np.zeros((H, W), np.float32)
    if hand_at:
        hx, hy = hand_at
        for k in range(5):                                                    # pressed in the same place, day after day
            stamp(hand, rot(mitten(1.0, seed + k), r.uniform(-8, 8) + 12), hx * W + r.normal(0, 14), hy * H + r.normal(0, 14), 0.75)
        m = np.maximum(m, hand * hand_strength)
    return np.clip(m, 0, 1), np.clip(hand, 0, 1)

# hand print: right of centre, at the height of a sitting plush's head (0.10 m above the bed of a 0.55 m pane)
front, hand = build(7, hand_at=(0.90, 1 - 0.17), hand_strength=0.62)
Image.fromarray((front * 255).astype(np.uint8)).save(os.path.join(OUT, "glass_front.png"))
Image.fromarray((hand * 255).astype(np.uint8)).save(os.path.join(OUT, "glass_hand.png"))
side, _ = build(21)
Image.fromarray((side * 255).astype(np.uint8)).save(os.path.join(OUT, "glass_side.png"))
Image.fromarray((front * 255).astype(np.uint8)).resize((800, 733)).save(os.path.join(OUT, "glass_front_preview.jpg"))
print("ok")
