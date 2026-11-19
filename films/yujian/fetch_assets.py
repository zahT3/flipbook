"""Download the Poly Haven textures (all CC0) this film uses.
  python3 films/yujian/fetch_assets.py
"""
import json, os, urllib.request
IDS = ["polar_fleece", "curly_teddy_natural", "ribbed_corduroy", "gingham_check", "knitted_fleece", "wool_boucle",
       "terry_cloth", "velour_velvet", "blue_metal_plate", "metal_plate", "cotton_jersey", "painted_metal_shutter"]
MAPS = {"Diffuse": "diff", "nor_gl": "nor", "Rough": "rough", "Displacement": "disp"}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "polyhaven")
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "music2mv-film"}), timeout=60).read()
for i in IDS:
    files = json.loads(get("https://api.polyhaven.com/files/" + i))
    d = os.path.join(ROOT, i); os.makedirs(d, exist_ok=True)
    for key, short in MAPS.items():
        if key not in files: print("  no", key, "for", i); continue
        u = files[key]["1k"]["jpg"]["url"]
        fp = os.path.join(d, short + ".jpg")
        if not os.path.exists(fp): open(fp, "wb").write(get(u))
    print(i, sorted(os.listdir(d)), [k for k in files if k not in ("blend", "gltf", "mtlx")])
