"""Step 1: read the named beaches, merge pieces of the same beach (same name, same country, within MERGE_M), and list the
vector tiles within NEAR_KM of every beach. Output: SCR/beaches.pkl (shapely geometries), SCR/tiles_needed.json."""
import gzip, pickle
from collections import defaultdict
import numpy as np
from shapely import wkt
from shapely.geometry import Point
from shapely.ops import unary_union
from common import *


def lit(s):
    s = s.strip()
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^.*)?$', s, re.S)
    v = m.group(1) if m else s
    return v.replace('\\"', '"').replace("\\\\", "\\")


rows = []
with gzip.open(f"{RAW}/beaches.tsv.gz", "rt", encoding="utf-8") as f:
    next(f)
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) < 5: continue
        g = wkt.loads(lit(c[4]))
        if g.geom_type == "GeometryCollection":
            g = unary_union([x.buffer(0) if x.geom_type.endswith("Polygon") else x for x in g.geoms])
        if not g.is_valid: g = g.buffer(0)
        rows.append({"cc": lit(c[0]), "osm": c[1].strip("<>").replace("https://www.openstreetmap.org/", ""), "name": lit(c[2]).strip(),
                     "surface": lit(c[3]), "g": g})
print("rows", len(rows))


def key(n):
    return re.sub(r"\s+", " ", n.lower().replace("’", "'")).strip()


groups = defaultdict(list)
for r in rows:
    groups[(r["cc"], key(r["name"]))].append(r)
beaches = []
for (cc, k), rs in groups.items():
    # single-linkage clusters of pieces within MERGE_M (degrees approximated at the latitude)
    left = list(range(len(rs))); clusters = []
    while left:
        cl = [left.pop(0)]; changed = True
        while changed:
            changed = False
            for j in left[:]:
                gj = rs[j]["g"]
                lat = gj.centroid.y; s = 111320 * math.cos(math.radians(lat))
                if any(rs[i]["g"].distance(gj) * s < MERGE_M for i in cl):
                    cl.append(j); left.remove(j); changed = True
        clusters.append(cl)
    for cl in clusters:
        g = unary_union([rs[i]["g"] for i in cl])
        surf = sorted(set(rs[i]["surface"] for i in cl if rs[i]["surface"]))
        beaches.append({"cc": cc, "name": rs[cl[0]]["name"], "osm": [rs[i]["osm"] for i in cl], "surface": ";".join(surf), "g": g,
                        "lon": g.centroid.x, "lat": g.centroid.y})
beaches.sort(key=lambda b: (b["cc"], b["name"], b["lat"]))
for i, b in enumerate(beaches):
    b["id"] = i
print("beaches after merging", len(beaches), "pieces merged", len(rows) - len(beaches))
need = set()
for b in beaches:
    dlat = (NEAR_KM + 2) * 1000 / 111195; dlon = dlat / math.cos(math.radians(b["lat"]))
    x0, y1 = tile_of(b["lon"] - dlon, b["lat"] - dlat); x1, y0 = tile_of(b["lon"] + dlon, b["lat"] + dlat)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            need.add((x, y))
print("tiles needed at z", Z, len(need))
pickle.dump(beaches, open(f"{SCR}/beaches.pkl", "wb"))
jsave(sorted(need), f"{SCR}/tiles_needed.json")
