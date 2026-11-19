"""Post: hold each drawing two frames, bloom, grade, grain, gate weave, the one dissolve, fades, subtitles; encode with the mix.

  python3 films/yujian/post.py <frames_dir> <out.mp4> [--audio out/yujian/mix.wav] [--nosub] [--from 0 --to 701] [--crf 15]
Frames are 0000.png ... 0701.png, one per twelfth of a second. Missing frames are skipped (handy for per-shot previews).
The last drawing is held HOLD more drawings, so the picture stays a full second after the last move; the music has ended by then.
"""
import sys, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def opt(k, d=None): return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
src, out = sys.argv[1], sys.argv[2]
SPF, FPS, N = 12, 24, 702
F0, F1 = int(opt("--from", 0)), int(opt("--to", N - 1))
AUDIO = opt("--audio", "out/yujian/clip.wav")
FONT = "/System/Library/Fonts/Supplemental/Songti.ttc"
DISSOLVE_AT, DISSOLVE_N = 655, 6            # shot 11 -> 12: six drawings
FADE_IN, FADE_OUT = 0.5, 0.55
HOLD = 6                                    # drawings: the claw stops moving at 57.25 s; with these the fade starts at 58.45
# Subtitles: inputs/yujian/subtitles.tsv, one line per subtitle: clip seconds in <tab> out <tab> text.
# Not kept with the code (the lyrics are copyrighted); without the file the film comes out without subtitles.
SUBS = opt("--subs", "inputs/yujian/subtitles.tsv")
LYRICS = []
if os.path.exists(SUBS):
    for ln in open(SUBS, encoding="utf-8"):
        if ln.strip() and not ln.startswith("#"):
            a, b, text = ln.rstrip("\n").split("\t")
            LYRICS.append((float(a), float(b), text))
else:
    print("no subtitles file at", SUBS)

def path(f): return os.path.join(src, "%04d.png" % f)
first = next(f for f in range(F0, F1 + 1) if os.path.exists(path(f)))
W, H = Image.open(path(first)).size
k = W / 1920.0
def load(f): return np.asarray(Image.open(path(f)).convert("RGB"), np.float32) / 255.0

def bloom(a):
    """Soft glow from the bulbs and neon."""
    hi = np.clip((a - 0.78) / 0.22, 0, 1) ** 1.6 * a
    small = Image.fromarray((hi * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    g1 = np.asarray(small.filter(ImageFilter.GaussianBlur(2.5 * k)).resize((W, H), Image.BILINEAR), np.float32) / 255
    g2 = np.asarray(small.filter(ImageFilter.GaussianBlur(10 * k)).resize((W, H), Image.BILINEAR), np.float32) / 255
    return 1 - (1 - a) * (1 - np.clip(0.30 * g1 + 0.42 * g2, 0, 1))

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vig = 1 - 0.20 * np.clip(((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) / 0.5, 0, 1)[..., None]

def grade(a):
    """A light print look: a soft S-curve, a little more colour, cool shadows against warm highlights."""
    a = np.clip(a, 0, 1)
    a = a + 0.30 * a * (1 - a) * (2 * a - 1)
    lum = a.mean(-1, keepdims=True)
    a = lum + (a - lum) * 1.07
    a = a + (1 - lum) ** 2 * np.array([-0.012, 0.003, 0.016], np.float32) + lum ** 2 * np.array([0.012, 0.004, -0.014], np.float32)
    return a

def weave(a, f):
    """Gate weave: each drawing sits a fraction of a pixel off, as on a camera stand."""
    r = np.random.default_rng(f * 7 + 1)
    dx, dy = r.normal(0, 0.45 * k), r.normal(0, 0.45 * k)
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    im = im.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, dy), resample=Image.BICUBIC)
    return np.asarray(im, np.float32) / 255

def grain(a, f):
    r = np.random.default_rng(f * 13 + 5)
    g = r.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray(g, "F").resize((W, H), Image.BILINEAR))
    lum = a.mean(-1, keepdims=True)
    return a + g[..., None] * 0.016 * (0.35 + 1.3 * lum * (1 - lum) * 2)

_sub = {}
def subtitle(text):
    if text in _sub: return _sub[text]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    font = ImageFont.truetype(FONT, round(38 * k), index=0)
    d = ImageDraw.Draw(im)
    sp = round(5 * k)
    widths = [d.textlength(c, font=font) for c in text]
    tw = sum(widths) + sp * (len(text) - 1)
    x, y = (W - tw) / 2, H - round(96 * k)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    cx = x
    for c, w in zip(text, widths):
        ds.text((cx, y + 1.5 * k), c, font=font, fill=(20, 10, 6, 210)); cx += w + sp
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(3.5 * k)))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(1.2 * k)))
    d = ImageDraw.Draw(im); cx = x
    for c, w in zip(text, widths):
        d.text((cx, y), c, font=font, fill=(255, 243, 226, 238)); cx += w + sp
    _sub[text] = np.asarray(im, np.float32) / 255
    return _sub[text]

hold = HOLD if F1 == N - 1 else 0
TOTAL = (N + hold) / SPF
t_off = F0 / SPF
dur = (F1 - F0 + 1 + hold) / SPF
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-"]
has_audio = bool(AUDIO) and os.path.exists(AUDIO)
if has_audio: cmd += ["-ss", "%.3f" % t_off, "-t", "%.3f" % dur, "-i", AUDIO]
cmd += ["-c:v", "libx264", "-crf", opt("--crf", "15"), "-preset", "slow", "-pix_fmt", "yuv420p"]
if has_audio: cmd += ["-af", "apad", "-c:a", "aac", "-b:a", "256k", "-shortest"]      # silence under the held last drawing
cmd += ["-movflags", "+faststart", out]
ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
nosub = "--nosub" in sys.argv
prev_last = None
last = None
held = None
for f in range(F0, F1 + 1 + hold):
    if f >= N:                               # the held drawing: same picture, fresh grain and weave
        a = last = grain(weave(held, f), f)
    elif os.path.exists(path(f)):
        a = load(f)
        if f == DISSOLVE_AT - 1: prev_last = a.copy()
        if DISSOLVE_AT <= f < DISSOLVE_AT + DISSOLVE_N and prev_last is not None:
            m = 1 - (f - DISSOLVE_AT + 1) / (DISSOLVE_N + 1)
            a = a * (1 - m) + prev_last * m
        a = held = grade(bloom(a) * vig)
        a = grain(weave(a, f), f)
        last = a
    elif last is None: continue
    else: a = last
    for sub in range(FPS // SPF):
        t = f / SPF + sub / FPS
        b = a
        if F0 == 0: b = b * min(1.0, t / FADE_IN) ** 1.4
        if F1 == N - 1: b = b * float(np.clip((TOTAL - t) / FADE_OUT, 0, 1)) ** 1.3
        if not nosub:
            for (t0, t1, text) in LYRICS:
                if t0 - 0.05 <= t <= t1 + 0.3:
                    al = min(1, (t - t0 + 0.05) / 0.25) * min(1, (t1 + 0.3 - t) / 0.3)
                    s = subtitle(text)
                    al_map = s[..., 3:4] * al
                    b = b * (1 - al_map) + s[..., :3] * al_map
        ff.stdin.write((np.clip(b, 0, 1) * 255).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait()
print("wrote", out)
