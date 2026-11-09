"""Step 2: fetch the OpenFreeMap zoom-10 tiles near the beaches one at a time, rasterise the sea (water layer, class ocean) to a
MPX x MPX mask, keep island and islet names from the place layer, and delete each tile as soon as it is read, so the cache
never holds more than a few tiles. Output: MASKS/<x>_<y>.npy (packed bits), SCR/islands.json, SCR/tiles_version.json."""
import sys, time, urllib.request
import numpy as np
import mapbox_vector_tile as mvt
from rasterio.features import rasterize
from shapely.geometry import shape
from shapely.affinity import scale
from concurrent.futures import ThreadPoolExecutor
from common import *

tj = json.load(urllib.request.urlopen(urllib.request.Request("https://tiles.openfreemap.org/planet", headers=UA)))
URL = tj["tiles"][0]
VERSION = URL.split("/")[-4]
jsave({"tiles_url": URL, "version": VERSION}, f"{SCR}/tiles_version.json")
need = [tuple(t) for t in jload(f"{SCR}/tiles_needed.json")]


def fetch(t):
    x, y = t
    out = f"{MASKS}/{x}_{y}.npy"
    if os.path.exists(out):
        return None
    for k in range(6):
        try:
            b = urllib.request.urlopen(urllib.request.Request(URL.format(z=Z, x=x, y=y), headers=UA), timeout=60).read()
            break
        except Exception:
            time.sleep(2 + 4 * k)
    else:
        raise RuntimeError(f"tile {t}")
    tmp = f"{TILES}/{x}_{y}.pbf"
    open(tmp, "wb").write(b)                     # the per-tile cache: written, read and deleted at once
    d = mvt.decode(open(tmp, "rb").read(), default_options={"y_coord_down": True})
    os.remove(tmp)
    shapes = []
    W = d.get("water", {})
    ext = W.get("extent", 4096)
    for f in W.get("features", []):
        if f["properties"].get("class") != "ocean":
            continue
        g = scale(shape(f["geometry"]), MPX / ext, MPX / ext, origin=(0, 0))
        shapes.append((g, 1))
    m = rasterize(shapes, out_shape=(MPX, MPX), fill=0, dtype="uint8", all_touched=False) if shapes else np.zeros((MPX, MPX), np.uint8)
    np.save(out, np.packbits(m.astype(bool), axis=None))
    isl = []
    P = d.get("place", {})
    pe = P.get("extent", 4096)
    n = 2 ** Z
    for f in P.get("features", []):
        if f["properties"].get("class") in ("island", "islet") and f["geometry"]["type"] == "Point":
            px, py = f["geometry"]["coordinates"]
            gx = x + px / pe; gy = y + py / pe
            lon = gx / n * 360 - 180; lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * gy / n))))
            isl.append({"name": f["properties"].get("name:en") or f["properties"].get("name"), "lon": lon, "lat": lat, "cls": f["properties"]["class"]})
    return len(b), isl


t0 = time.time()
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(fetch, need))
got = [r for r in res if r]
isl = jload(f"{SCR}/islands.json") if os.path.exists(f"{SCR}/islands.json") else []
for r in got:
    isl += r[1]
seen, uniq = set(), []
for i in isl:
    k = (i["name"], round(i["lon"], 3), round(i["lat"], 3))
    if k not in seen and i["name"]:
        seen.add(k); uniq.append(i)
jsave(uniq, f"{SCR}/islands.json", keepdash=True)
print("tiles", len(need), "fetched now", len(got), "MB", round(sum(r[0] for r in got) / 1e6, 1), "islands", len(uniq), round(time.time() - t0), "s")
assert not os.listdir(TILES)
