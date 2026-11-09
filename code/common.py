"""Shared paths, constants and helpers for the sea-sunsets study ("Where the sun sets into the sea").

Inputs (read in place, never modified):
  RAW/beaches.tsv.gz   OpenStreetMap natural=beach with a name in the UK (GB) and Ireland (IE): country, OSM id, name, surface,
                       full WKT geometry (QLever export; ODbL).
  OFM vector tiles     https://tiles.openfreemap.org/planet (OpenMapTiles schema, OpenStreetMap, ODbL) at zoom Z: the water
                       layer, class ocean, for the sea out to NEAR_KM from each beach; place layer for island names. Cached in
                       TILES (outside the repo) and deleted after use.
  DEM                  /home/claude/newdata/raw_new8/terrain/tiles/10/{x}/{y}.png: AWS Terrain Tiles, Terrarium encoding
                       (height = R*256 + G + B/256 - 32768 m), zoom 10, about 90 m, with bathymetry below 0. Land heights
                       along each ray, and land beyond NEAR_KM.
  SETTLE               /home/claude/newdata/raw_new8/uk_settlements.tsv: Wikidata UK settlements (nearest town in popups).
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("SS_RAW", "/home/claude/newdata/raw_new10")
GEO = os.environ.get("SS_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("SS_FONTS", "/home/claude/ref/fonts")
INK = os.environ.get("SS_INK", "/home/claude/studies/ink-map")
INKFONTS = os.path.join(INK, "fonts", "ttf")
DEM = os.environ.get("SS_DEM", "/home/claude/newdata/raw_new8/terrain/tiles/10")
SETTLE = os.environ.get("SS_SETTLE", "/home/claude/newdata/raw_new8/uk_settlements.tsv")
SCR = os.environ.get("SS_SCRATCH", "/home/claude/scratch/sea-sunsets")
TILES = os.path.join(SCR, "tiles")
MASKS = os.path.join(SCR, "masks")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
for d in (DATA, IMG, SCR, TILES, MASKS):
    os.makedirs(d, exist_ok=True)

SLUG = "sea-sunsets"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
UA = {"User-Agent": "sea-sunsets-study/1.0 (research; maps.tristanhotham.com)"}
Z = 10                      # vector tile zoom for the sea
MPX = 1024                  # mask pixels per tile edge (about 24 m at 50 N, 19 m at 60 N)
NEAR_KM = 12.0              # sea polygons this far out; terrain beyond
FAR_KM = 150.0              # rays end here: land farther away is below the horizon unless over 1,300 m high
EYE_M = 3.0                 # eye height above the sea, standing on a beach
K_REFR = 0.13               # refraction coefficient: effective Earth radius R / (1 - k)
R_EARTH = 6371000.0
R_EFF = R_EARTH / (1 - K_REFR)
H0 = -0.833                 # apparent altitude of the Sun's centre at sunrise and sunset (refraction + semi-diameter)
YEAR = 2026
MERGE_M = 1000.0            # pieces of the same named beach closer than this are one beach
AZ_STEP = 0.25              # degrees between rays


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, list):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None, keepdash=False):
    obj = nonan(obj) if keepdash else dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    raise ValueError(f)


# ---------- web mercator tile and pixel coordinates
def lonlat_to_px(lon, lat, z, size):
    """global pixel coordinates (float) at zoom z with `size` pixels per tile"""
    import numpy as np
    n = 2 ** z * size
    lat = np.clip(lat, -85, 85)
    x = (np.asarray(lon) + 180.0) / 360.0 * n
    y = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * n
    return x, y


def tile_of(lon, lat, z=Z):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)


def destination(lon, lat, az_deg, d_m):
    """great-circle destination (numpy-broadcast)"""
    import numpy as np
    p1, l1 = np.radians(lat), np.radians(lon)
    a, dr = np.radians(az_deg), np.asarray(d_m) / R_EARTH
    p2 = np.arcsin(np.sin(p1) * np.cos(dr) + np.cos(p1) * np.sin(dr) * np.cos(a))
    l2 = l1 + np.arctan2(np.sin(a) * np.sin(dr) * np.cos(p1), np.cos(dr) - np.sin(p1) * np.sin(p2))
    return np.degrees(l2), np.degrees(p2)


# ---------- the Sun: declination through the year (NOAA / Spencer 1971) and the rise and set azimuths
def declination(doy):
    import numpy as np
    g = 2 * np.pi / 365 * (np.asarray(doy) - 1)
    return np.degrees(0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g)
                      - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))


def rise_set_az(lat, dec, h0=H0):
    """azimuths (degrees from true north) of sunrise and sunset for declination dec; nan if the Sun does not rise or set"""
    import numpy as np
    p, d, h = np.radians(lat), np.radians(dec), np.radians(h0)
    c = (np.sin(d) - np.sin(p) * np.sin(h)) / (np.cos(p) * np.cos(h))
    a = np.degrees(np.arccos(np.where(np.abs(c) <= 1, c, np.nan)))
    return a, 360 - a


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
