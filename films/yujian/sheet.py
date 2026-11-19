"""Contact sheet from rendered stills.  python3 films/yujian/sheet.py <dir> <out.jpg> [--cols 6] [--w 480] [--glob 't*.png']"""
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
def opt(k, d): return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
cols, w = int(opt("--cols", 6)), int(opt("--w", 480))
files = sorted(glob.glob(os.path.join(src, opt("--glob", "*.png"))))
if not files: sys.exit("no files")
im0 = Image.open(files[0]); h = round(w * im0.height / im0.width)
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB").resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    label = os.path.splitext(os.path.basename(f))[0]
    if label.isdigit(): label = "%s  %.2fs" % (label, int(label) / 12)
    d.rectangle((0, 0, 9 * len(label) + 10, 22), fill=(0, 0, 0)); d.text((5, 2), label, font=font, fill=(255, 235, 150))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out, quality=88)
print(out, len(files))
