"""One contact sheet per shot, every drawing.  python3 films/yujian/shot_sheets.py <frames_dir> <out_dir> [shot ...]"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
SHOTS = [(0, "s1"), (40, "s2"), (90, "s3a"), (123, "s3b"), (138, "s3c"), (154, "s4"), (215, "s5a"), (235, "s5b"), (256, "s5c"), (280, "s6"),
         (341, "s7a"), (372, "s7b"), (405, "s8a"), (431, "s8b"), (451, "s8c"), (467, "s9a"), (487, "s9b"), (532, "s10a"),
         (568, "s10b"), (593, "s10c"), (619, "s11"), (655, "s12"), (702, "end")]
src, out = sys.argv[1], sys.argv[2]
want = sys.argv[3:]
os.makedirs(out, exist_ok=True)
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
W = 320
for (f0, name), (f1, _) in zip(SHOTS, SHOTS[1:]):
    if want and name not in want: continue
    files = [(f, os.path.join(src, "%04d.png" % f)) for f in range(f0, f1)]
    files = [(f, p) for f, p in files if os.path.exists(p)]
    if not files: continue
    cols = 6
    im0 = Image.open(files[0][1]); H = round(W * im0.height / im0.width)
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W, rows * H), (15, 15, 15))
    for i, (f, p) in enumerate(files):
        im = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(im); lab = "%.2f" % (f / 12)
        d.rectangle((0, 0, 44, 17), fill=(0, 0, 0)); d.text((3, 1), lab, font=font, fill=(255, 235, 150))
        sheet.paste(im, ((i % cols) * W, (i // cols) * H))
    sheet.save(os.path.join(out, "%s.jpg" % name), quality=85)
    print(name, len(files))
