"""Step 3b: what is in the way. For every blocked bearing, decide whether the land is the beach's own coast (the same piece
of land in the sea mask within NEAR_KM, e.g. the headland at the end of the bay, or the rest of the island a beach is on), the
mainland (Great Britain, Ireland or France: Natural Earth polygons of 10,000 km2 or more), or another island, named from the
OpenStreetMap island place nearest the middle of that island's Natural Earth polygon (or, for islands too small for Natural
Earth, the nearest island or islet place within 4 km). Output: updates the 'names' of SCR/rays.pkl in place."""
import pickle, time
import numpy as np
from scipy import ndimage
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

RAYS = pickle.load(open(f"{SCR}/rays.pkl", "rb"))
BEACH = {b["id"]: b for b in pickle.load(open(f"{SCR}/beaches.pkl", "rb"))}
from rasterio.features import rasterize
from shapely.ops import transform as stf
have = {tuple(map(int, f[:-4].split("_"))) for f in os.listdir(MASKS)}


def local_mask(lon, lat, rad_km):
    dlat = rad_km * 1000 / 111195; dlon = dlat / math.cos(math.radians(lat))
    xa, yb = tile_of(lon - dlon, lat - dlat); xb, ya = tile_of(lon + dlon, lat + dlat)
    M = np.zeros(((yb - ya + 1) * MPX, (xb - xa + 1) * MPX), bool)
    for x in range(xa, xb + 1):
        for y in range(ya, yb + 1):
            if (x, y) in have:
                M[(y - ya) * MPX:(y - ya + 1) * MPX, (x - xa) * MPX:(x - xa + 1) * MPX] = np.unpackbits(np.load(f"{MASKS}/{x}_{y}.npy"))[:MPX * MPX].reshape(MPX, MPX).astype(bool)
    return M, xa * MPX, ya * MPX


polys = []
for f in jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]:
    if f["properties"]["ADM0_A3"] not in ("GBR", "IRL", "IMN", "FRA", "GGY", "JEY"):
        continue
    g = shape(f["geometry"])
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        polys.append((p, p.area * 111.2 ** 2 * math.cos(math.radians(p.centroid.y))))
TREE = STRtree([p for p, _ in polys])
ISL = jload(f"{SCR}/islands.json")
ISLA = np.array([[i["lon"], i["lat"]] for i in ISL])
PT = STRtree([Point(*a) for a in ISLA])
_pn = {}


def poly_name(pi):
    if pi not in _pn:
        p = polys[pi][0]; c = p.representative_point()
        inside = [int(k) for k in PT.query(p.buffer(0.01)) if p.buffer(0.01).contains(Point(*ISLA[k]))]
        big = [k for k in inside if ISL[k]["cls"] == "island"] or inside
        _pn[pi] = ISL[min(big, key=lambda k: (ISLA[k][0] - c.x) ** 2 + (ISLA[k][1] - c.y) ** 2)]["name"] if big else ""
        # checked by eye: the place nearest the middle of Jura is an islet; the Isle of Man has no island place in the tiles
        if _pn[pi] == "Eilean Ard" and polys[pi][1] > 300: _pn[pi] = "Jura"
        if p.contains(Point(-4.5, 54.2)): _pn[pi] = "Isle of Man"
    return _pn[pi]


def ne_poly(lon, lat):
    pt = Point(lon, lat); pi = int(TREE.nearest(pt))
    return pi if polys[pi][0].distance(pt) < 0.03 else None


def name_of(lon, lat, own_pi):
    pi = ne_poly(lon, lat)
    if pi is not None:
        if polys[pi][1] >= 10000: return "mainland"
        if pi == own_pi: return "coast"
        return "island:" + poly_name(pi)
    d = (ISLA[:, 0] - lon) ** 2 * math.cos(math.radians(lat)) ** 2 + (ISLA[:, 1] - lat) ** 2
    k = int(np.argmin(d))
    return "island:" + (ISL[k]["name"] if d[k] < (4 / 111.2) ** 2 else "")


t0 = time.time(); stats = {"coast": 0, "mainland": 0, "island": 0}
for j, (bid, r) in enumerate(RAYS.items()):
    if not r or r.get("inland"): continue
    M, ox, oy = local_mask(r["olon"], r["olat"], NEAR_KM + 1.5)
    lab, _ = ndimage.label(~M, structure=np.ones((3, 3)))
    px, py = lonlat_to_px(r["olon"], r["olat"], Z, MPX)
    oc, orow = int(px - ox), int(py - oy)
    # the beach's own land: the land component that the beach itself touches most (the beach outline widened by three
    # pixels), so that a rock or islet just off the beach is not taken for the beach's own island (review fix: Inishbofin,
    # St Agnes); if the beach touches no land, the land component nearest the observer
    gp = stf(lambda x, y, z=None: (lambda q: (q[0] - ox, q[1] - oy))(lonlat_to_px(np.asarray(x), np.asarray(y), Z, MPX)), BEACH[bid]["g"])
    if gp.geom_type in ("Point", "MultiPoint", "LineString", "MultiLineString"):
        gp = gp.buffer(2)
    bm = ndimage.binary_dilation(rasterize([(gp, 1)], out_shape=M.shape, fill=0, dtype="uint8", all_touched=True).astype(bool), iterations=3)
    labs = lab[bm & (lab > 0)]
    if labs.size:
        own = int(np.bincount(labs).argmax())
    else:
        _, (ir, ic) = ndimage.distance_transform_edt(M[max(0, orow - 80):orow + 80, max(0, oc - 80):oc + 80], return_indices=True)
        rr, cc = orow - max(0, orow - 80), oc - max(0, oc - 80)
        own = lab[max(0, orow - 80) + ir[rr, cc], max(0, oc - 80) + ic[rr, cc]]
    own_pi = ne_poly(r["olon"], r["olat"])
    if own_pi is not None and polys[own_pi][1] >= 10000: own_pi = -1
    # the name of the island the beach is on (if any): its Natural Earth polygon's name, or the nearest OSM island place;
    # blocking rocks and islets that take that same name (separate specks of land in the mask) count as the beach's own coast
    if own_pi is not None and own_pi != -1:
        own_name = "island:" + poly_name(own_pi)
    else:
        own_name = name_of(r["olon"], r["olat"], None) if own_pi is None else None
        if own_name == "mainland": own_name = None
    for ev in ("rise", "set"):
        R = r[ev]; nm = {}
        for i in R["names"]:
            lo, la = float(R["blon"][i]), float(R["blat"][i])
            if not np.isfinite(lo): nm[i] = ""; continue
            if R["block_m"][i] < NEAR_KM * 1000:
                qx, qy = lonlat_to_px(lo, la, Z, MPX); c_, r_ = int(qx - ox), int(qy - oy)
                if 0 <= r_ < lab.shape[0] and 0 <= c_ < lab.shape[1] and own and lab[r_, c_] == own:
                    nm[i] = "coast"; stats["coast"] += 1; continue
            n = name_of(lo, la, own_pi)
            if n == "mainland" and own_pi == -1 and R["block_m"][i] < NEAR_KM * 1000:
                n = "coast"
            if own_name and n == own_name and own_name != "island:":
                n = "coast"
            nm[i] = n; stats["mainland" if n in ("mainland", "coast") else "island"] += 1
        R["names"] = nm
    if j % 300 == 0: print(j, round(time.time() - t0), "s", flush=True)
pickle.dump(RAYS, open(f"{SCR}/rays.pkl", "wb"))
print("done", stats, round(time.time() - t0), "s")
