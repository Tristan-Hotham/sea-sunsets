"""Step 3: for every beach, a point at the water's edge and a fan of rays over the bearings where the Sun rises and sets in the
year; along each ray, the first land that stands above the sea horizon. Then, day by day, whether the Sun sets into (or rises
out of) the open sea. Output: SCR/rays.pkl.

Geometry. The observer stands EYE_M above the sea at the sea pixel nearest the middle of the beach, at least two mask pixels
(about 40 m) from land. Out to NEAR_KM the sea is the OpenFreeMap ocean polygon rasterised at about 20 m; any other pixel is
land, at least 5 m high or the terrain height if higher. Beyond NEAR_KM, land is wherever the terrain tile is above 0 m.
A land sample at distance d and height h blocks the horizon when its elevation angle (h - EYE)/d - d/(2 R_eff) exceeds the
angle of the sea horizon, -sqrt(2 EYE / R_eff), with refraction k = K_REFR."""
import pickle, time
import numpy as np
from PIL import Image
from scipy import ndimage
from rasterio.features import rasterize
from shapely.geometry import shape, Point
from shapely.affinity import affine_transform
from shapely.prepared import prep
from shapely.strtree import STRtree
from common import *

beaches = pickle.load(open(f"{SCR}/beaches.pkl", "rb"))
ONLY = os.environ.get("SS_ONLY")              # test on a few beaches by name: SS_ONLY="Fistral Beach|Tynemouth Longsands"
if ONLY:
    beaches = [b for b in beaches if re.search(ONLY, b["name"])]
have = {tuple(map(int, f[:-4].split("_"))) for f in os.listdir(MASKS)}
_mask = {}


def mask_tile(x, y):
    if (x, y) not in _mask:
        if (x, y) in have:
            _mask[(x, y)] = np.unpackbits(np.load(f"{MASKS}/{x}_{y}.npy"))[:MPX * MPX].reshape(MPX, MPX).astype(bool)
        else:
            _mask[(x, y)] = None
    return _mask[(x, y)]


# ---------- terrain: one mosaic of every zoom-10 tile (int16 metres; missing = sea)
TX = sorted(int(d) for d in os.listdir(DEM))
TY = sorted({int(f[:-4]) for x in TX for f in os.listdir(f"{DEM}/{x}")})
tx0, ty0 = TX[0], TY[0]
DEMA = np.full(((TY[-1] - ty0 + 1) * 256, (TX[-1] - tx0 + 1) * 256), -10, np.int16)
t0 = time.time()
for x in TX:
    for f in os.listdir(f"{DEM}/{x}"):
        y = int(f[:-4])
        a = np.asarray(Image.open(f"{DEM}/{x}/{f}").convert("RGB")).astype(np.float32)
        h = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        DEMA[(y - ty0) * 256:(y - ty0 + 1) * 256, (x - tx0) * 256:(x - tx0 + 1) * 256] = np.clip(np.round(h), -9999, 9999).astype(np.int16)
print("terrain mosaic", DEMA.shape, round(time.time() - t0), "s")


def elev(lon, lat):
    px, py = lonlat_to_px(lon, lat, 10, 256)
    c = np.floor(px - tx0 * 256).astype(int); r = np.floor(py - ty0 * 256).astype(int)
    ok = (r >= 0) & (r < DEMA.shape[0]) & (c >= 0) & (c < DEMA.shape[1])
    out = np.full(np.shape(px), -10, np.int16)
    out[ok] = DEMA[r[ok], c[ok]]
    return out


# ---------- islands for naming what blocks the Sun: Natural Earth polygons (islands are those under 10,000 km2) + OSM place names
ne = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
polys = []
for f in ne:
    if f["properties"]["ADM0_A3"] not in ("GBR", "IRL", "IMN", "FRA", "GGY", "JEY", "NOR", "NLD", "BEL"):
        continue
    g = shape(f["geometry"])
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        lat = p.centroid.y
        km2 = p.area * 111.2 ** 2 * math.cos(math.radians(lat))
        polys.append((p, km2))
TREE = STRtree([p for p, _ in polys])
ISL = jload(f"{SCR}/islands.json")
ISLA = np.array([[i["lon"], i["lat"]] for i in ISL])


from functools import lru_cache
PT_TREE = STRtree([Point(*a) for a in ISLA]) if len(ISL) else None
_inpoly = {}


def islands_in(pi):
    if pi not in _inpoly:
        p = polys[pi][0].buffer(0.01)
        _inpoly[pi] = [int(k) for k in PT_TREE.query(p) if p.contains(Point(*ISLA[k]))]
    return _inpoly[pi]


def blocker_name(lon, lat):
    return _blocker_name(round(lon, 2), round(lat, 2))


@lru_cache(maxsize=None)
def _blocker_name(lon, lat):
    """'mainland' (Great Britain, Ireland, France...), 'island:<name>' for an island (a Natural Earth polygon under 10,000 km2,
    or land on no Natural Earth polygon at all, named from the nearest OSM island or islet place), or 'island:' unnamed"""
    pt = Point(lon, lat)
    pi = int(TREE.nearest(pt))
    p, km2 = polys[pi]
    if p.distance(pt) < 0.03:
        if km2 >= 10000:
            return "mainland"
        inside = islands_in(pi)
        if inside:
            cand = [k for k in inside if ISL[k]["cls"] == "island"] or inside
            k = min(cand, key=lambda k: (ISLA[k][0] - lon) ** 2 + (ISLA[k][1] - lat) ** 2)
            return "island:" + ISL[k]["name"]
    d = (ISLA[:, 0] - lon) ** 2 * math.cos(math.radians(lat)) ** 2 + (ISLA[:, 1] - lat) ** 2
    k = int(np.argmin(d))
    return "island:" + (ISL[k]["name"] if d[k] < (4 / 111.2) ** 2 else "")


def local_mask(lon, lat, rad_km):
    """mosaic of the sea mask around a point; returns (mask, global pixel origin x, y)"""
    dlat = rad_km * 1000 / 111195; dlon = dlat / math.cos(math.radians(lat))
    xa, yb = tile_of(lon - dlon, lat - dlat); xb, ya = tile_of(lon + dlon, lat + dlat)
    M = np.zeros(((yb - ya + 1) * MPX, (xb - xa + 1) * MPX), bool)
    for x in range(xa, xb + 1):
        for y in range(ya, yb + 1):
            t = mask_tile(x, y)
            if t is not None:
                M[(y - ya) * MPX:(y - ya + 1) * MPX, (x - xa) * MPX:(x - xa + 1) * MPX] = t
    return M, xa * MPX, ya * MPX


DIP = math.sqrt(2 * EYE_M / R_EFF)
DOY = np.arange(1, 366)
DEC = declination(DOY)
H0D = H0 - math.degrees(DIP)                   # the sea horizon is a little below the astronomical one


def rays_for(b):
    lon0, lat0 = b["lon"], b["lat"]
    M, ox, oy = local_mask(lon0, lat0, NEAR_KM + 1.5)
    # beach pixels and the observer: the sea pixel (two pixels clear of land) nearest the beach, near its middle
    def to_px(x, y, z=None):
        px, py = lonlat_to_px(np.asarray(x), np.asarray(y), Z, MPX)
        return px - ox, py - oy
    from shapely.ops import transform as stf
    g = b["g"]
    gp = stf(lambda x, y, z=None: to_px(x, y), g)
    if gp.geom_type in ("Point", "MultiPoint", "LineString", "MultiLineString"):
        gp = gp.buffer(2)
    bm = rasterize([(gp, 1)], out_shape=M.shape, fill=0, dtype="uint8", all_touched=True).astype(bool)
    sea2 = ndimage.binary_erosion(M, iterations=2)
    if not sea2.any():
        return None
    # distance (pixels) from every pixel to the beach
    dist_b, _ = ndimage.distance_transform_edt(~bm, return_indices=True) if bm.any() else (None, None)
    if dist_b is None:
        return None
    cand = np.where(sea2, dist_b, np.inf)
    dmin = cand.min()
    mpp = 40075016.7 * math.cos(math.radians(lat0)) / (2 ** Z * MPX)        # metres per mask pixel
    if not np.isfinite(dmin) or dmin * mpp > 600:
        return {"inland": True, "near_sea_m": None if not np.isfinite(dmin) else float(dmin * mpp)}
    # candidates: sea pixels (two pixels clear of land) along the seaward edge of the beach, up to 12 spread along it;
    # the observer is the one with the most open bearings over the year's sunset and sunrise arcs in the first 3 km
    n = 2 ** Z * MPX
    ys, xs = np.where(cand <= dmin + 3)
    if len(xs) > 12:
        u = np.c_[xs, ys].astype(float); u0 = u - u.mean(0)
        ax_ = np.linalg.svd(u0, full_matrices=False)[2][0]
        order = np.argsort(u0 @ ax_); pick = order[np.linspace(0, len(order) - 1, 12).round().astype(int)]
        xs, ys = xs[pick], ys[pick]
    ar, as_ = rise_set_az(lat0, DEC, H0D)
    azs = np.r_[np.arange(np.nanmin(ar), np.nanmax(ar), 1.0), np.arange(np.nanmin(as_), np.nanmax(as_), 1.0)]
    d3 = np.arange(1, 150) * 20.0
    best, score = 0, -1
    for k in range(len(xs)):
        lo = (xs[k] + 0.5 + ox) / n * 360 - 180; la = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ys[k] + 0.5 + oy) / n))))
        L1, L2 = destination(lo, la, azs[:, None], d3[None, :])
        qx, qy = to_px(L1, L2); c_ = np.floor(qx).astype(int); r_ = np.floor(qy).astype(int)
        ok = (r_ >= 0) & (r_ < M.shape[0]) & (c_ >= 0) & (c_ < M.shape[1])
        s_ = np.zeros(c_.shape, bool); s_[ok] = M[r_[ok], c_[ok]]
        sc = int(s_.all(1).sum())
        if sc > score: best, score = k, sc
    oxp, oyp = xs[best] + 0.5, ys[best] + 0.5
    olon = (oxp + ox) / n * 360 - 180
    olat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (oyp + oy) / n))))
    # bearings: the whole year's sunrise and sunset arcs at this latitude, plus a margin
    ar, as_ = rise_set_az(olat, DEC, H0D)
    arcs = {"rise": (np.floor(np.nanmin(ar)) - 1, np.ceil(np.nanmax(ar)) + 1), "set": (np.floor(np.nanmin(as_)) - 1, np.ceil(np.nanmax(as_)) + 1)}
    out = {"inland": False, "olon": olon, "olat": olat, "edge_m": float(dmin * mpp), "mpp": mpp}
    dn = np.arange(1, int(NEAR_KM * 1000 / 20)) * 20.0                      # every 20 m out to NEAR_KM
    df = np.arange(NEAR_KM * 1000, FAR_KM * 1000 + 1, 150.0)                # every 150 m beyond
    for ev, (a0, a1) in arcs.items():
        az = np.arange(a0, a1 + 1e-9, AZ_STEP)
        LON, LAT = destination(olon, olat, az[:, None], dn[None, :])
        px, py = to_px(LON, LAT)
        c = np.floor(px).astype(int); r = np.floor(py).astype(int)
        inside = (r >= 0) & (r < M.shape[0]) & (c >= 0) & (c < M.shape[1])
        sea = np.zeros(c.shape, bool); sea[inside] = M[r[inside], c[inside]]
        hn = np.maximum(elev(LON, LAT).astype(float), 5.0)
        angn = np.where(~sea, (hn - EYE_M) / dn[None, :] - dn[None, :] / (2 * R_EFF), -9)
        LONf, LATf = destination(olon, olat, az[:, None], df[None, :])
        hf = elev(LONf, LATf).astype(float)
        angf = np.where(hf > 0, (hf - EYE_M) / df[None, :] - df[None, :] / (2 * R_EFF), -9)
        ang = np.concatenate([angn, angf], 1); dd = np.concatenate([dn, df])
        blk = ang > -DIP
        first = np.where(blk.any(1), blk.argmax(1), -1)
        bd = np.where(first >= 0, dd[np.maximum(first, 0)], np.nan)
        blon = np.where(first >= 0, np.concatenate([LON, LONf], 1)[np.arange(len(az)), np.maximum(first, 0)], np.nan)
        blat = np.where(first >= 0, np.concatenate([LAT, LATf], 1)[np.arange(len(az)), np.maximum(first, 0)], np.nan)
        out[ev] = {"az": az, "block_m": bd, "blon": blon, "blat": blat}
    # day by day
    for ev, A in (("rise", ar), ("set", as_)):
        R = out[ev]
        i = np.clip(np.round((A - R["az"][0]) / AZ_STEP).astype(int), 0, len(R["az"]) - 1)
        R["day_az"] = A
        R["day_block_m"] = np.where(np.isnan(A), np.nan, R["block_m"][i])
        R["day_open"] = np.isfinite(A) & np.isnan(R["day_block_m"])
        R["day_idx"] = i
    return out


t0 = time.time()
res = {}
for j, b in enumerate(beaches):
    try:
        res[b["id"]] = rays_for(b)
    except Exception as e:
        print("fail", b["name"], e); res[b["id"]] = None
    if j % 200 == 0:
        print(j, round(time.time() - t0), "s", flush=True)
        _mask.clear()
# names of what blocks: per beach and event, cluster the blocked days by blocker
for b in beaches:
    r = res.get(b["id"])
    if not r or r.get("inland"): continue
    for ev in ("rise", "set"):
        R = r[ev]
        nm = {}
        for i in np.unique(R["day_idx"][~R["day_open"] & np.isfinite(R["day_az"])]):
            nm[int(i)] = blocker_name(float(R["blon"][i]), float(R["blat"][i])) if np.isfinite(R["blon"][i]) else ""
        R["names"] = nm
pickle.dump(res, open(f"{SCR}/rays{'_test' if ONLY else ''}.pkl", "wb"))
print("done", len(res), round(time.time() - t0), "s", "inland", sum(1 for r in res.values() if r and r.get("inland")), "failed", sum(1 for r in res.values() if r is None))
