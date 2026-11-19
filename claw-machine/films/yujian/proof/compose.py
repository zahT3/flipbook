"""The proof film: the finished frame peeled back to clay, wires, primitives and code; time frozen and the camera
taken round the machine; the dog built line by line; the animation curves; the review rounds; the numbers.

  python3 films/yujian/proof/compose.py --fmt v|h [--from 0 --to 81.3] [--out ...] [--still 12.5]
Inputs (small; the big renders were turned into videos on the Mac Studio):
  out/yujian/yujian-claw.mp4                 the film
  out/yujian/proof/src/raw_0505.png          drawing 505 straight out of the renderer (no grade, no grain)
  out/yujian/proof/src/{clay,nofur,wire}.png the same drawing with the materials swapped (proof/render.py --mode layers)
  out/yujian/proof/src/{explode,orbit,build}.mp4   12 fps sequences from proof/render.py
  out/yujian/proof/data.json                 proof/dump.py: the claw's channels for all 702 drawings, fur counts
  out/yujian/process/*.mp4                   review previews and the shot-10b before/after
Streams every frame to ffmpeg; nothing is written to disk but the mp4.
"""
import sys, os, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
def P(*a): return os.path.join(ROOT, *a)
def opt(k, d=None): return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
FMT = opt("--fmt", "v")
W, H = (1080, 1920) if FMT == "v" else (1920, 1080)
FPS = 24
SRC = opt("--src", P("out/yujian/proof/src"))
SONG = P("inputs/yujian/song.m4a")
FILM = P("out/yujian/yujian-claw.mp4")
DATA = json.load(open(P("out/yujian/proof/data.json")))

SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"
_f = {}
def font(kind, size):
    k = (kind, size)
    if k not in _f:
        _f[k] = ImageFont.truetype(MENLO if kind.startswith("mono") else SONGTI, size,
                                   index={"bold": 1, "light": 3, "black": 0, "mono": 0, "monob": 1}[kind])
    return _f[k]

# ------------------------------------------------------------------ sources
class Video:
    """Forward reader of a video at its own frame rate; get(i) returns frame i (RGB PIL), re-seeking if asked to go back."""
    def __init__(self, path, fps=24, size=None):
        self.path, self.fps = path, fps
        pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True)
        self.w, self.h = map(int, pr.stdout.strip().split(","))
        pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path], capture_output=True, text=True)
        self.n = int(pr.stdout.strip())
        self.p = None; self.pos = 0; self.last = None; self.last_i = -1
    def _open(self, i):
        if self.p: self.p.kill()
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", "%.4f" % (i / self.fps), "-i", self.path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE, bufsize=self.w * self.h * 3 * 2)
        self.pos = i
    def get(self, i):
        i = max(0, min(self.n - 1, int(i)))
        if i == self.last_i: return self.last
        if self.p is None or i < self.pos or i > self.pos + 48: self._open(i)
        while self.pos <= i:
            buf = self.p.stdout.read(self.w * self.h * 3)
            if len(buf) < self.w * self.h * 3: return self.last          # past the end: hold
            self.pos += 1
            if self.pos - 1 == i: self.last = Image.frombuffer("RGB", (self.w, self.h), buf, "raw", "RGB", 0, 1)
        self.last_i = i
        return self.last

_v = {}
def video(path, fps=24):
    if path not in _v: _v[path] = Video(path, fps)
    return _v[path]
_im = {}
def still(path):
    if path not in _im: _im[path] = Image.open(path).convert("RGB")
    return _im[path]

def film_at(ft):                      # the finished film at film time ft
    return video(FILM).get(round(ft * FPS))
def seq(name, k):                     # a 12 fps render sequence, drawing k
    return video(os.path.join(SRC, name + ".mp4"), 12).get(k)

# ------------------------------------------------------------------ layout
def crop_sq(im, cx=960, zoom=1.0):
    """Square crop of a 16:9 frame around x = cx (in 1920 coordinates), as a 1080 square."""
    s = im.width / 1920.0
    side = 1080 * s / zoom
    x0 = min(max(cx * s - side / 2, 0), im.width - side); y0 = (im.height - side) / 2
    return im.resize((1080, 1080), Image.LANCZOS, box=(x0, y0, x0 + side, y0 + side))
def full(im, zoom=1.0, cx=960, cy=540):
    s = im.width / 1920.0
    w, h = 1920 * s / zoom, 1080 * s / zoom
    x0 = min(max(cx * s - w / 2, 0), im.width - w); y0 = min(max(cy * s - h / 2, 0), im.height - h)
    return im.resize((1920, 1080), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))

PIC_V = (0, 330)                      # where the square picture sits in the vertical frame
def picture(canvas, im, cx=960, zoom=1.0):
    """The main picture: a square in the vertical film, the whole frame in the horizontal one."""
    if FMT == "v": canvas.paste(crop_sq(im, cx, zoom), PIC_V)
    else: canvas.paste(full(im, zoom))

def blank(col=(10, 9, 12)): return Image.new("RGB", (W, H), col)

def fade_alpha(t, t0, t1, fin=0.25, fout=0.25):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin if fin else 1.0, (t1 - t) / fout if fout else 1.0)

def text_img(s, fnt, fill=(255, 245, 230), shadow=True, maxw=None, spacing=1.25):
    """A block of text (lines wrapped to maxw) as an RGBA image with a soft shadow."""
    lines = []
    for para in s.split("\n"):
        if maxw is None: lines.append(para); continue
        import re
        cur = ""
        for tok in re.findall(r"[A-Za-z0-9_.()\-]+|.", para):
            if fnt.getlength(cur + tok) > maxw and cur.strip(): lines.append(cur); cur = tok.lstrip()
            else: cur += tok
        lines.append(cur)
    lh = int(fnt.size * spacing)
    w = int(max([fnt.getlength(l) for l in lines] + [1])) + 16
    h = lh * len(lines) + 16
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
        for i, l in enumerate(lines): ds.text((8, 8 + i * lh + 2), l, font=fnt, fill=(0, 0, 0, 230))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(max(2, fnt.size // 10))))
        d = ImageDraw.Draw(im)
    for i, l in enumerate(lines): d.text((8, 8 + i * lh), l, font=fnt, fill=fill)
    return im
_t = {}
def put_text(canvas, s, kind, size, xy, alpha=1.0, anchor="lt", fill=(255, 245, 230), maxw=None, shadow=True):
    if alpha <= 0: return
    k = (s, kind, size, fill, maxw, shadow)
    if k not in _t: _t[k] = text_img(s, font(kind, size), fill, shadow, maxw)
    im = _t[k]
    x, y = xy
    if anchor[0] == "m": x -= im.width // 2
    if anchor[0] == "r": x -= im.width
    if anchor[1] == "b": y -= im.height
    if anchor[1] == "m": y -= im.height // 2
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    canvas.paste(im, (int(x), int(y)), im)

def caption(canvas, t, items, sub_top=False):
    """items: [(t0, t1, title, sub)]. Vertical: title above the picture, the line under it below the picture
    (or under the title, sub_top). Horizontal: top left over the picture (the film's own lyrics are at the bottom)."""
    for (t0, t1, title, sub) in items:
        a = fade_alpha(t, t0, t1)
        if a <= 0: continue
        if FMT == "v":
            put_text(canvas, title, "bold", 66, (W // 2, 150 if sub_top else 175), a, "mt", maxw=1000)
            if sub:
                if sub_top: put_text(canvas, sub, "light", 38, (W // 2, 248), a, "mt", fill=(235, 225, 210), maxw=1000)
                else: put_text(canvas, sub, "light", 44, (W // 2, PIC_V[1] + 1080 + 50), a, "mt", fill=(240, 230, 214), maxw=960)
        else:
            dark = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
            g = np.linspace(170 * a, 0, 260).astype(np.uint8)
            dark.putalpha(Image.fromarray(np.repeat(g[:, None], W, 1)))
            canvas.paste(dark, (0, 0), dark)
            put_text(canvas, title, "bold", 54, (70, 40), a, "lt", maxw=1700)
            if sub: put_text(canvas, sub, "light", 36, (72, 122), a, "lt", fill=(240, 230, 214), maxw=1700)

def ease(p): p = min(1, max(0, p)); return p * p * (3 - 2 * p)

# ------------------------------------------------------------------ code panels
def code_lines(path, nums):
    src = open(P("films/yujian", path)).read().split("\n")
    return [(n, src[n - 1].rstrip()) for n in nums]
def code_block(canvas, box, header, lines, size, alpha=1.0, hi=None):
    """Code with its real line numbers, wrapped to the box. hi: set of line numbers drawn bright."""
    x0, y0, x1, y1 = box
    fn, fb = font("mono", size), font("monob", size)
    cw = fn.getlength("M"); lh = int(size * 1.42)
    gut = int(cw * 5)
    maxc = max(20, int((x1 - x0 - gut) / cw))
    panel = Image.new("RGBA", (x1 - x0, y1 - y0), (14, 13, 18, int(215 * alpha)))
    d = ImageDraw.Draw(panel)
    d.text((14, 10), header, font=fb, fill=(240, 180, 120, int(255 * alpha)))
    y = 14 + lh + 6
    for n, s in lines:
        ind = len(s) - len(s.lstrip())
        body = s.strip()
        chunks = []
        first = maxc - ind
        while body:
            take = first if not chunks else maxc - ind - 4
            chunks.append(body[:take]); body = body[take:]
        bright = hi is None or n in hi
        col = (238, 232, 220) if bright else (120, 118, 125)
        for j, c in enumerate(chunks or [""]):
            if y + lh > y1 - y0 - 6: break
            if j == 0: d.text((10, y), "%4d" % n, font=fn, fill=(110, 106, 118, int(255 * alpha)))
            pre = " " * ind + ("    " if j else "")
            if body is not None and c.lstrip().startswith("#"): cc = (140, 170, 140)
            else: cc = col
            d.text((10 + gut, y), pre + c, font=fn, fill=(*cc, int(255 * alpha)))
            y += lh
    canvas.paste(panel, (x0, y0), panel)

# ------------------------------------------------------------------ segments (times in seconds of the proof film)
# The cuts sit on the song's bar lines. Bars from the beats measured on the song (out/yujian/beats.json, about 92 BPM),
# counted from the first line of the clip ("阴天", song 54.22 s). The music starts on the pick-up of "我想 我等 我期待"
# and ends on the bar line before the vocals come back after the piano interlude.
MUSIC_START = 35.45
_beats = json.load(open(P("out/yujian/beats.json")))["beats"]
_i0 = min(range(len(_beats)), key=lambda i: abs(_beats[i] - 54.22))
B = [d - MUSIC_START for d in _beats[_i0 % 4::4] if 36.0 < d < 106.8][1:]      # B[0] ends the hook (pick-up + one bar), B[-1] = the end
T_LAYERS, T_SYNC, T_ORBIT, T_BUILD, T_CURVES, T_REVIEW, T_10B, T_END, T_TOTAL = B[0], B[6], B[8], B[11], B[16], B[19], B[21], B[23], B[26]
HELD = 505                            # the drawing that gets peeled: the claw carrying the dog
CX_HELD = 1000

def layer_img(name):
    if name == "final": return film_at(HELD / 12)
    if name == "raw": return still(os.path.join(SRC, "raw_0505.png"))
    return still(os.path.join(SRC, name + ".png"))

LAYER_CUTS = [(B[0], "raw"), (B[1], "clay"), (B[2], "nofur"), (B[3], "wire"), (B[4], "explode")]
T_CODE = B[5]
LAYER_CAPS = [(B[0] + 0.15, B[1] - 0.1, "① 去掉调色和颗粒", "这是渲染器直接出的图"),
              (B[1] + 0.15, B[2] - 0.1, "② 去掉布纹贴图", "只剩形状和灯光"),
              (B[2] + 0.15, B[3] - 0.1, "③ 去掉毛", "小狗身上 %d 万根毛，是程序按面积撒上去的" % round(DATA["fur"]["dog"] / 1e4)),
              (B[3] + 0.15, B[4] - 0.1, "④ 线框", "每一个面都是脚本算出来的网格"),
              (B[4] + 0.15, B[5] - 0.1, "⑤ 拆开", "椭球、圆柱、方块、管子：全是基本形状"),
              (B[5] + 0.15, B[6] - 0.15, "⑥ 停在生成它们的代码上", "建模、摆姿势、打灯，都在这几个 .py 文件里")]
LAYER_CODE = [("yj/plush.py", list(range(146, 151))), ("yj/claw.py", [61, 62, 65]), ("yj/anim.py", [537, 539, 540, 542])]

def seg_layers(c, t):
    # the current layer and the one being wiped in
    names = ["final"] + [n for _, n in LAYER_CUTS]
    idx = sum(1 for tc, _ in LAYER_CUTS if t >= tc)
    def img(i, t):
        n = names[i]
        if n == "explode":
            k = int(max(0, (t - B[4] - 0.45) * 12))
            return seq("explode", min(11, k))
        return layer_img(n)
    cur = img(idx, t)
    canvas = c
    picture(canvas, cur, CX_HELD)
    if idx > 0:
        tc = LAYER_CUTS[idx - 1][0]
        p = (t - tc) / 0.45
        if p < 1:                     # wipe: the new layer comes in from the left with a bright line
            prev = blank(); picture(prev, img(idx - 1, t), CX_HELD)
            nxt = canvas.copy()
            x = int(ease(p) * W)
            canvas.paste(prev); canvas.paste(nxt.crop((0, 0, x, H)), (0, 0))
            ImageDraw.Draw(canvas).rectangle((x - 2, PIC_V[1] if FMT == "v" else 0, x + 2, PIC_V[1] + 1080 if FMT == "v" else H), fill=(255, 235, 200))
    if t >= T_CODE:                   # the code layer over the dimmed parts
        a = ease((t - T_CODE) / 0.5)
        dim = Image.new("RGBA", (W, H), (8, 7, 10, int(170 * a)))
        canvas.paste(dim, (0, 0), dim)
        lines = []
        for path, nums in LAYER_CODE: lines += [(0, "# " + path)] + code_lines(path, nums)
        box = (30, PIC_V[1] + 40, W - 30, PIC_V[1] + 1040) if FMT == "v" else (120, 230, 1800, 1000)
        code_block2(canvas, box, lines, 25 if FMT == "v" else 27, a)
    caption(canvas, t, LAYER_CAPS)
    if FMT == "v":
        steps = ["成片", "渲染", "灰模", "去毛", "线框", "拆开", "代码"]
        cur_i = idx + (1 if t >= T_CODE else 0)
        x = 60; y = 1700
        for i, st_ in enumerate(steps):
            col = (255, 205, 150) if i == cur_i else ((200, 194, 186) if i < cur_i else (95, 92, 100))
            fnt = font("bold", 40)
            ImageDraw.Draw(canvas).text((x, y), st_, font=fnt, fill=col)
            x += int(fnt.getlength(st_)) + 18
            if i < len(steps) - 1:
                ImageDraw.Draw(canvas).text((x, y), "›", font=fnt, fill=(95, 92, 100)); x += 34

def code_block2(canvas, box, lines, size, alpha):
    """Several files in one block: entries with n == 0 are file headers."""
    x0, y0, x1, y1 = box
    fn, fb = font("mono", size), font("monob", size)
    cw = fn.getlength("M"); lh = int(size * 1.42); gut = int(cw * 5)
    maxc = int((x1 - x0 - gut) / cw)
    d = ImageDraw.Draw(canvas)
    y = y0
    for n, s in lines:
        if n == 0:
            y += lh // 3
            d.text((x0, y), s[2:], font=fb, fill=(240, 180, 120)); y += lh; continue
        ind = len(s) - len(s.lstrip()); body = s.strip()
        first = True
        while body and y < y1:
            take = maxc - ind - (0 if first else 4)
            if first: d.text((x0, y), "%4d" % n, font=fn, fill=(115, 110, 122))
            d.text((x0 + gut, y), " " * ind + ("" if first else "    ") + body[:take], font=fn, fill=(236, 230, 218))
            body = body[take:]; first = False; y += lh

def seg_hook(c, t):
    p = t / T_LAYERS
    picture(c, film_at(HELD / 12), CX_HELD, 1.0 + 0.04 * (1 - p))
    caption(c, t, [(0.15, T_LAYERS - 0.1, "这条片子里没有一张生成的图", "形状、动作、灯光，都是代码搭出来、算出来、渲出来的")])

ORBIT_N = 72
def seg_orbit(c, t):
    lt = t - T_ORBIT
    if lt < 0.9:
        picture(c, film_at(24 / 12), 1060)
    else:
        k = int((lt - 0.9) * 12)
        im = seq("orbit", min(ORBIT_N - 1, k))
        picture(c, im, 960)
        if lt < 1.15:                 # a quick dissolve from the film's shot into the orbit
            a = (lt - 0.9) / 0.25
            prev = blank(); picture(prev, film_at(24 / 12), 1060)
            c.paste(Image.blend(prev, c, a))
    if FMT == "v" and lt >= 0.9:
        ang = min(360, (lt - 0.9) * 12 / ORBIT_N * 360)
        d = ImageDraw.Draw(c); y = 1720
        d.rounded_rectangle((90, y, 990, y + 14), 7, fill=(45, 43, 50))
        d.rounded_rectangle((90, y, 90 + 900 * ang / 360, y + 14), 7, fill=(255, 200, 140))
        put_text(c, "摄影机转了 %d°" % ang, "bold", 38, (W // 2, y + 40), 1.0, "mt", fill=(225, 218, 206))
    caption(c, t, [(T_ORBIT + 0.1, T_ORBIT + 1.0, "⑧ 让时间停在第 2 秒", "爪子正夹住小狗"),
                   (T_ORBIT + 1.2, T_BUILD - 0.15, "摄影机绕机器转一圈", "每个角度都是同一个三维场景渲出来的；背面没封板，像定格动画的布景")])

BUILD_PER = 16
BUILD_STEPS = [("身体：一个椭球", [133, 143, 144, 145, 146]),
               ("头：又一个椭球", [134, 148, 149]),
               ("嘴：小椭球、鼻子、三段缝线", [151, 153, 155, 156]),
               ("眼睛：一颗珠子，一颗旧纽扣", [159, 160, 161, 162]),
               ("缝线：沿着曲面一针一针排", [163, 164, 169, 170, 171]),
               ("耳朵：压扁的椭球，挂在铰链上", [172, 173, 174, 179, 182, 183, 186, 187]),
               ("腿：四个椭球", [188, 190, 192, 193]),
               ("尾巴、项圈、铜扣", [196, 197, 200, 204, 206, 208]),
               ("毛：%d 万根，按面积撒" % round(DATA["fur"]["dog"] / 1e4), [147, 150, 30, 36, 41, 44])]
def seg_build(c, t):
    lt = t - T_BUILD
    k = max(0, int(lt * 12))
    step = min(len(BUILD_STEPS) - 1, k // BUILD_PER)
    im = seq("build", min(BUILD_PER * 10 - 1, k))
    title, nums = BUILD_STEPS[step]
    lines = code_lines("yj/plush.py", nums)
    if FMT == "v":
        c.paste(crop_sq(im, 960), PIC_V)
        code_block(c, (24, 1440, W - 24, 1890), "yj/plush.py  build_dog()", lines, 24)
        caption(c, t, [(T_BUILD + 0.05, T_BUILD + 2.2, "⑨ 小狗是这样一行行搭出来的", "yj/plush.py 第 130–210 行")] if lt < 1.7 else [(T_BUILD, T_CURVES - 0.1, "%d / 9  %s" % (step + 1, title), None)], sub_top=True)
    else:
        c.paste(crop_sq(im, 960), (0, 0))
        code_block(c, (1100, 300, 1900, 1050), "yj/plush.py  build_dog()", lines, 28)
        a = fade_alpha(t, T_BUILD + 0.05, T_CURVES - 0.15)
        put_text(c, "⑨ 小狗是这样一行行搭出来的", "bold", 46, (1110, 60), a)
        put_text(c, "%d / 9  %s" % (step + 1, title), "bold", 40, (1110, 170), a, fill=(255, 210, 160), maxw=780)

CURVE_FT0 = 38.6                      # film time shown at the start of the curves segment
def channel(f):
    d = DATA["frames"][max(0, min(701, f))]
    return d["z"] * 100, d["open"][0]
def plot(c, box, ft, which, label, unit, lo, hi, col):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(c)
    d.rectangle(box, fill=(18, 17, 22))
    span = 2.5
    def X(tt): return x0 + (tt - (ft - span)) / (2 * span) * (x1 - x0)
    def Y(v): return y1 - 18 - (v - lo) / (hi - lo) * (y1 - y0 - 60)
    # one flat step per drawing: each drawing is held for two film frames
    f0, f1 = int((ft - span) * 12) - 1, int((ft + span) * 12) + 1
    pts = []
    for f in range(f0, f1 + 1):
        v = channel(f)[which]
        pts += [(X(f / 12), Y(v)), (X((f + 1) / 12), Y(v))]
    pts = [(min(max(x, x0), x1), y) for x, y in pts]
    d.line(pts, fill=col, width=4)
    d.line((X(ft), y0 + 44, X(ft), y1 - 8), fill=(255, 255, 255), width=2)
    f = int(ft * 12); v = channel(f)[which]
    d.ellipse((X(ft) - 8, Y(v) - 8, X(ft) + 8, Y(v) + 8), fill=col)
    d.text((x0 + 14, y0 + 8), label, font=font("bold", 28), fill=(235, 228, 216))
    d.text((x1 - 14, y0 + 10), "%.1f %s" % (v, unit), font=font("mono", 26), fill=col, anchor="ra")
def seg_curves(c, t):
    lt = t - T_CURVES
    ft = CURVE_FT0 + lt
    fr = film_at(ft)
    drawing = int(ft * 12); sub = int(ft * 24) % 2 + 1
    if FMT == "v":
        c.paste(crop_sq(fr, 900), PIC_V)
        plot(c, (24, 1440, W - 24, 1655), ft, 0, "爪子高度", "cm", 13, 32, (120, 200, 255))
        plot(c, (24, 1675, W - 24, 1890), ft, 1, "指头张角", "°", -12, 70, (255, 170, 110))
        put_text(c, "第 %d 张画 · 第 %d/2 帧" % (drawing, sub), "bold", 36, (W - 30, PIC_V[1] + 20), 1.0, "rt")
    else:
        c.paste(fr.resize((1152, 648), Image.LANCZOS), (40, 240))
        plot(c, (1230, 240, 1880, 550), ft, 0, "爪子高度", "cm", 13, 32, (120, 200, 255))
        plot(c, (1230, 578, 1880, 888), ft, 1, "指头张角", "°", -12, 70, (255, 170, 110))
        put_text(c, "第 %d 张画 · 第 %d/2 帧" % (drawing, sub), "bold", 36, (1180, 256), 1.0, "rt")
    caption(c, t, [(T_CURVES + 0.05, B[17] - 0.1, "⑩ 动作是算出来的", "没有手摆关键帧：pose(t) 按时间算出每一张的姿态"),
                   (B[17] + 0.05, T_REVIEW - 0.15, "一秒 12 张，每张停两帧", "曲线是一级级的台阶：定格动画的节奏")], sub_top=True)

ROUNDS = [("process/round1-preview-full.mp4", "第 1 轮预览"), ("process/round2-preview-full.mp4", "第 2 轮预览"),
          ("process/round3-preview-full.mp4", "第 3 轮预览"), (None, "成片")]
REV_FT0 = 23.4
def seg_review(c, t):
    lt = t - T_REVIEW
    ft = REV_FT0 + min(lt, 5.0)
    cells = []
    for path, lab in ROUNDS:
        im = film_at(ft) if path is None else video(P("out/yujian", path)).get(round(ft * 24))
        cells.append((im, lab))
    if FMT == "v":
        for (im, lab), y in ((cells[0], 340), (cells[3], 966)):
            c.paste(im.resize((1080, 608), Image.LANCZOS), (0, y)); label(c, lab, (18, y + 14))
        put_text(c, "第 2、3 轮预览略", "light", 30, (W - 30, 1590), 0.8, "rt", fill=(190, 184, 176))
    else:
        for i, (im, lab) in enumerate(cells):
            x, y = 180 + (i % 2) * 782, 200 + (i // 2) * 441
            c.paste(im.resize((780, 439), Image.LANCZOS), (x, y)); label(c, lab, (x + 14, y + 14))
    caption(c, t, [(T_REVIEW + 0.05, T_10B - 0.1, "⑪ 每一轮都逐格审片", "同一个镜头，第 1 轮预览和成片：机位、构图、动作都改过" if FMT == "v" else "同一个镜头：三轮预览（480×270）和成片。机位、构图、动作都改过")], sub_top=True)

def label(c, s, xy, col=(255, 245, 230)):
    fnt = font("bold", 38); w = int(fnt.getlength(s)) + 28
    box = Image.new("RGBA", (w, 58), (0, 0, 0, 165)); c.paste(box, xy, box)
    ImageDraw.Draw(c).text((xy[0] + 14, xy[1] + 8), s, font=fnt, fill=col)

def seg_10b(c, t):
    lt = t - T_10B
    loop = (T_END - T_10B) / 2
    k = min(49, int((lt % loop) * 50 / loop))
    bef = video(P("out/yujian/process/shot10b-before.mp4")).get(k)
    aft = video(P("out/yujian/process/shot10b-after.mp4")).get(k)
    if FMT == "v":
        c.paste(bef.resize((1080, 608), Image.LANCZOS), (0, 340)); c.paste(aft.resize((1080, 608), Image.LANCZOS), (0, 966))
        label(c, "改前", (18, 354), (255, 150, 130)); label(c, "改后", (18, 980), (160, 235, 170))
    else:
        c.paste(bef.resize((940, 529), Image.LANCZOS), (20, 260)); c.paste(aft.resize((940, 529), Image.LANCZOS), (960, 260))
        label(c, "改前", (36, 276), (255, 150, 130)); label(c, "改后", (976, 276), (160, 235, 170))
    caption(c, t, [(T_10B + 0.05, T_10B + (T_END - T_10B) / 2 - 0.05, "⑫ 修穿模：先量，再改", "改前小狗的头穿过了挡板"),
                   (T_10B + (T_END - T_10B) / 2 + 0.05, T_END - 0.15, "量出来：门洞和小狗一样高", "都是 13 厘米：挡板改成往下翻，全片复查 0 处")], sub_top=True)

NUM3 = [("2,643", "行 Python"), ("%d 万" % round(sum(DATA["fur"].values()) / 1e4), "根毛，13 只布偶"), ("0 处", "穿模，702 张逐张检查")]
AUTHOR = "github.com/zahT3"          # where the author (and the code) lives: a small mark in the corner, and in the end credit
CREDIT = "%s · made with Claude Fable 5.2" % AUTHOR      # Menlo has no Chinese: the credit stays in English
NOTE = "用 Blender 建模和渲染，全部由 Python 脚本驱动 · 没有下载或生成任何模型、图片、视频 · 布纹贴图来自 Poly Haven CC0"
NUM_T = 4.6
def seg_end(c, t):
    lt = t - T_END
    ft = 51.2 + lt
    picture(c, film_at(min(58.95, ft)), 960)
    a = fade_alpha(t, T_END + 0.05, T_END + NUM_T, 0.25, 0.4)
    if a > 0:                         # the numbers: big, white, over the film darkened almost to black
        dim = Image.new("RGBA", (W, H), (6, 5, 8, int(225 * a))); c.paste(dim, (0, 0), dim)
        for i, (big, small) in enumerate(NUM3):
            ai = a * ease((lt - 0.15 - i * 0.45) / 0.3)
            if FMT == "v":
                y = 470 + i * 380
                put_text(c, big, "black", 150, (W // 2, y), ai, "mt", fill=(255, 255, 255))
                put_text(c, small, "bold", 54, (W // 2, y + 190), ai, "mt", fill=(255, 214, 170))
            else:
                x = 330 + i * 630
                put_text(c, big, "black", 130, (x, 330), ai, "mt", fill=(255, 255, 255))
                put_text(c, small, "bold", 46, (x, 510), ai, "mt", fill=(255, 214, 170))
    b = fade_alpha(t, T_END + NUM_T + 0.3, T_TOTAL - 0.3, 0.4, 0.4)
    if FMT == "v":
        put_text(c, "《遇见》· 一支用代码做的定格动画", "bold", 50, (W // 2, 1520), b, "mt")
        put_text(c, NOTE.replace(" · ", "\n"), "light", 34, (W // 2, 1610), b, "mt", fill=(225, 218, 206))
        put_text(c, CREDIT, "monob", 30, (W // 2, 1790), b, "mt", fill=(255, 205, 150))
    else:
        if b > 0:
            band = Image.new("RGBA", (W, 340), (0, 0, 0, 0))
            band.putalpha(Image.fromarray(np.repeat((np.clip(np.linspace(0, 1.6, 340), 0, 1) * 215 * b).astype(np.uint8)[:, None], W, 1)))
            c.paste(band, (0, H - 340), band)
        put_text(c, "《遇见》· 一支用代码做的定格动画", "bold", 46, (W // 2, 945), b, "mb")
        put_text(c, CREDIT, "monob", 30, (W // 2, 885), b, "mb", fill=(255, 205, 150))
        first, rest = NOTE.split(" · ", 1)
        put_text(c, first + "\n" + rest, "light", 30, (W // 2, 1050), b, "mb", fill=(225, 218, 206))

SYNC0, SYNC1 = 6, 39                  # drawings re-rendered for the side-by-side passage (film 0.5-3.3 s: the first grab)
def seg_sync(c, t):
    lt = t - T_SYNC
    half = (T_ORBIT - T_SYNC) - (SYNC1 - SYNC0 - 4) / 12      # the second pass starts at drawing 10 and ends with the segment
    if lt < half:
        d = min(SYNC1, SYNC0 + int(lt * 12)); what, lab = "clay", "灰模"
    else:
        d = min(SYNC1, SYNC0 + 4 + int((lt - half) * 12)); what, lab = "wire", "线框"
    film = film_at(d / 12)
    other = seq("sync_" + what, d - SYNC0)
    if FMT == "v":
        c.paste(full(film, 1.25, 1020, 560).resize((1080, 608), Image.LANCZOS), (0, 330))
        c.paste(full(other, 1.25, 1020, 560).resize((1080, 608), Image.LANCZOS), (0, 956))
        label(c, "成片", (18, 344)); label(c, lab, (18, 970))
        put_text(c, "第 %d 张画" % d, "bold", 40, (W // 2, 1600), 1.0, "mt", fill=(225, 218, 206))
    else:
        c.paste(full(film, 1.25, 1020, 560).resize((940, 529), Image.LANCZOS), (20, 260))
        c.paste(full(other, 1.25, 1020, 560).resize((940, 529), Image.LANCZOS), (960, 260))
        label(c, "成片", (36, 276)); label(c, lab, (976, 276))
        put_text(c, "第 %d 张画" % d, "bold", 38, (W // 2, 820), 1.0, "mt", fill=(225, 218, 206))
    caption(c, t, [(T_SYNC + 0.05, T_SYNC + half - 0.05, "⑦ 同一段动作，逐张重渲成灰模", "成片第 0.5–3.3 秒，34 张画，和成片同步播放"),
                   (T_SYNC + half + 0.05, T_ORBIT - 0.15, "再渲一遍线框", "每一张的几何都和成片对得上")], sub_top=True)

SEGS = [(0.0, seg_hook), (T_LAYERS, seg_layers), (T_SYNC, seg_sync), (T_ORBIT, seg_orbit), (T_BUILD, seg_build), (T_CURVES, seg_curves),
        (T_REVIEW, seg_review), (T_10B, seg_10b), (T_END, seg_end)]
def mark():
    """The author's mark, top right on every frame: an orange block like a cursor, then the GitHub address in the
    same monospace as the code panels."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size = 28 if FMT == "v" else 26
    fnt = font("monob", size)
    d = ImageDraw.Draw(im)
    x, y = (W - 36, 46) if FMT == "v" else (W - 44, 34)
    w = fnt.getlength(AUTHOR)
    d.text((x + 2, y + 2), AUTHOR, font=fnt, fill=(0, 0, 0, 110), anchor="ra")
    d.text((x, y), AUTHOR, font=fnt, fill=(255, 250, 240, 200), anchor="ra")
    bx = x - w - 14 - size * 0.62
    d.rectangle((bx, y + size * 0.12, bx + size * 0.62, y + size * 1.02), fill=(221, 119, 91, 230))
    return im
MARK = mark()

def frame(t):
    c = blank()
    fn = [f for t0, f in SEGS if t >= t0][-1]
    fn(c, t)
    # hard cuts between sections, softened with a short dip at the joins
    for t0, _ in SEGS[1:]:
        if abs(t - t0) < 0.12 and t0 not in (T_LAYERS,):
            k = abs(t - t0) / 0.12
            c = Image.eval(c, lambda v, k=k: int(v * (0.35 + 0.65 * k)))
    if t > T_TOTAL - 0.5: c = Image.eval(c, lambda v, k=max(0, (T_TOTAL - t) / 0.5): int(v * k))
    c.paste(MARK, (0, 0), MARK)
    return c

if __name__ == "__main__":
    if opt("--mark-png"):                # the same mark for other videos (merge.sh puts it on the film)
        MARK.save(opt("--mark-png")); sys.exit()
    if opt("--still"):
        ts = [float(s) for s in opt("--still").split(",")]
        for s in ts:
            frame(s).save(opt("--out", "/tmp/proof_%s_%05.2f.jpg" % (FMT, s)), quality=90) if len(ts) == 1 else \
                frame(s).save("/tmp/yjt/still_%s_%05.2f.jpg" % (FMT, s), quality=88)
        sys.exit()
    t0, t1 = float(opt("--from", 0)), float(opt("--to", T_TOTAL))
    out = opt("--out", P("out/yujian/proof", "yujian-proof%s.mp4" % ("-vertical" if FMT == "v" else "")))
    dur = t1 - t0
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
           "-ss", "%.3f" % (MUSIC_START + t0), "-t", "%.3f" % dur, "-i", SONG,
           "-af", "volume=-2dB,afade=t=in:st=0:d=0.15,afade=t=out:st=%.2f:d=%.2f,alimiter=limit=-1.6dB:level=disabled" % (max(0, dur - (B[-1] - B[-2])), B[-1] - B[-2]),
           "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "224k", "-shortest", "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(round(dur * FPS))
    for i in range(n):
        ff.stdin.write(frame(t0 + i / FPS).tobytes())
        if i % 120 == 0: print("t=%.1f" % (t0 + i / FPS), flush=True)
    ff.stdin.close(); ff.wait()
    print("wrote", out)
