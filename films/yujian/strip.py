"""Strip of consecutive drawings.  python3 films/yujian/strip.py <frames_dir> <out.jpg> <f0> <f1> [--cols 4] [--w 480] [--step 1] [--crop x,y,w,h (fractions)]"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
src, out, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
def opt(k, d): return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
cols, w, step = int(opt("--cols", 4)), int(opt("--w", 480)), int(opt("--step", 1))
crop = [float(v) for v in opt("--crop", "0,0,1,1").split(",")]
fs = [f for f in range(f0, f1 + 1, step) if os.path.exists(os.path.join(src, "%04d.png" % f))]
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
ims = []
for f in fs:
    im = Image.open(os.path.join(src, "%04d.png" % f)).convert("RGB")
    W, H = im.size
    im = im.crop((int(crop[0] * W), int(crop[1] * H), int((crop[0] + crop[2]) * W), int((crop[1] + crop[3]) * H)))
    h = round(w * im.height / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im); lab = "%d  %.2f" % (f, f / 12)
    d.rectangle((0, 0, 9 * len(lab) + 8, 20), fill=(0, 0, 0)); d.text((4, 2), lab, font=font, fill=(255, 235, 150))
    ims.append(im)
h = ims[0].height
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), (15, 15, 15))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out, quality=88); print(out, len(ims))
