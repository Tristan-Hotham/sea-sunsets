"""Step 4: results per beach and overall. Output: data/results.json, data/beaches.csv, data/beaches.json (page),
Day strings: two characters per day of YEAR: '..' the Sun sets (or rises) over open sea; otherwise the distance to the
land in the way in units of 50 m, written in base 62 with the digits ALPH (most significant first)."""
import csv, pickle
from collections import Counter, defaultdict
import numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

ALPH = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
beaches = pickle.load(open(f"{SCR}/beaches.pkl", "rb"))
RAYS = pickle.load(open(f"{SCR}/rays.pkl", "rb"))
VER = jload(f"{SCR}/tiles_version.json")["version"]
OV = {}
if os.path.exists(f"{ROOT}/code/name_fixes.csv"):
    for r in csv.DictReader(open(f"{ROOT}/code/name_fixes.csv", encoding="utf-8")):
        OV[r["osm_name"]] = r["name"]

# places: county or council area and nation (Natural Earth admin 1), nearest UK town (Wikidata)
A1 = [f for f in jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"] if f["properties"]["adm0_a3"] in ("GBR", "IRL", "IMN")]
A1G = [shape(f["geometry"]) for f in A1]
A1T = STRtree(A1G)
towns = []
for line in open(SETTLE, encoding="utf-8").read().splitlines()[1:]:
    c = line.split("\t")
    m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", c[2])
    try: pop = float(c[3].strip('"').split("^")[0])
    except ValueError: continue
    if m and pop >= 2000:
        towns.append((re.sub(r'^"|"@en$', "", c[1]), float(m.group(1)), float(m.group(2)), pop))
TA = np.array([[t[1], t[2]] for t in towns])


def place_of(lon, lat):
    pt = Point(lon, lat)
    i = int(A1T.nearest(pt))
    p = A1[i]["properties"]
    nation = {"Ireland": "Ireland", "England": "England", "Scotland": "Scotland", "Wales": "Wales", "Northern Ireland": "Northern Ireland"}.get(p["geonunit"], p["geonunit"])
    if p["adm0_a3"] == "IMN": nation = "Isle of Man"
    if p["adm0_a3"] == "IRL": nation = "Ireland"          # Natural Earth leaves geonunit empty for Dún Laoghaire-Rathdown
    return {"North Ayshire": "North Ayrshire"}.get(p["name"], p["name"]).replace("\u2013", "-"), nation


def town_of(lon, lat):
    d = np.hypot((TA[:, 0] - lon) * math.cos(math.radians(lat)), TA[:, 1] - lat) * 111.2
    k = int(np.argmin(d))
    return (towns[k][0], round(float(d[k]), 1)) if d[k] <= 12 else (None, None)


def code(dm):
    if not np.isfinite(dm): return ".."
    k = int(np.clip(round(dm / 50), 1, 62 * 62 - 1))
    return ALPH[k // 62] + ALPH[k % 62]


def clean_name(n):
    n = n[7:] if n.startswith("island:") else n
    return OV.get(n, n)


# islands that share a name (two Inishbofins, in Galway and Donegal, for example) are told apart by where the blocking land
# lies: same-name blocking points more than 60 km apart get the county they lie in added to the name (review fix)
from collections import defaultdict as _dd
_pts = _dd(list)
for _r in RAYS.values():
    if not _r or _r.get("inland"): continue
    for _ev in ("set", "rise"):
        for _i, _n in _r[_ev]["names"].items():
            if _n.startswith("island:") and _n != "island:" and np.isfinite(_r[_ev]["blon"][_i]):
                _pts[_n].append((float(_r[_ev]["blon"][_i]), float(_r[_ev]["blat"][_i])))
_CL = {}
for _n, _p in _pts.items():
    cl = []
    for lo, la in _p:
        for c in cl:
            if math.hypot((lo - c[0]) * math.cos(math.radians(la)), la - c[1]) * 111.2 < 60: break
        else:
            cl.append((lo, la))
    if len(cl) > 1 and len({place_of(*c)[0] for c in cl}) > 1:      # a big island spanning 60 km stays one name
        _CL[_n] = cl
DUP_ISLANDS = {}


def island_label(n, lon, lat):
    """the island's name, with its county added when another island elsewhere has the same name"""
    if n not in _CL or not np.isfinite(lon):
        return clean_name(n)
    c = min(_CL[n], key=lambda c: math.hypot((lon - c[0]) * math.cos(math.radians(lat)), lat - c[1]))
    lab = f"{clean_name(n)} ({place_of(*c)[0]})"
    DUP_ISLANDS.setdefault(clean_name(n), set()).add(lab)
    return lab


rows, page = [], []
for b in beaches:
    r = RAYS.get(b["id"])
    base = {"id": b["id"], "name": b["name"], "cc": b["cc"], "surface": b["surface"], "osm": b["osm"], "lon": b["lon"], "lat": b["lat"]}
    if r is None or r.get("inland"):
        base.update({"status": "inland"}); rows.append(base); continue
    county, nation = place_of(r["olon"], r["olat"])
    town, tkm = town_of(r["olon"], r["olat"])
    rec = dict(base, status="coast", olon=r["olon"], olat=r["olat"], county=county, nation=nation, town=town, town_km=tkm)
    for ev in ("set", "rise"):
        R = r[ev]
        op = R["day_open"]
        rec[f"sea_{ev}_days"] = int(op.sum())
        names = []
        nm_day = []
        for d in range(365):
            if op[d]:
                nm_day.append(""); continue
            i = int(R["day_idx"][d]); n = R["names"].get(i, "")
            kind = "mainland" if n == "mainland" else ("island" if n.startswith("island") else "")
            nm_day.append(island_label(n, float(R["blon"][i]), float(R["blat"][i])) if kind == "island" else n)
        cnt = Counter(nm_day[d] for d in range(365) if not op[d])
        rec[f"{ev}_blockers"] = dict(cnt)
        isl = {k: v for k, v in cnt.items() if k not in ("mainland", "coast", "")}
        rec[f"{ev}_islands"] = isl
        rec[f"{ev}_unnamed_island_days"] = cnt.get("", 0)
        rec[f"{ev}_jun21"] = bool(op[171]); rec[f"{ev}_dec21"] = bool(op[354]); rec[f"{ev}_mar20"] = bool(op[78])
        rec[f"{ev}_az_jun21"] = float(R["day_az"][171]); rec[f"{ev}_az_dec21"] = float(R["day_az"][354])
        bm = R["day_block_m"][~op]
        rec[f"{ev}_block_med_km"] = float(np.median(bm) / 1000) if len(bm) else None
        rec[f"_{ev}_str"] = "".join(code(x) for x in R["day_block_m"])
        lst = sorted(set(x for x in nm_day if x))
        rec[f"_{ev}_names"] = lst
        rec[f"_{ev}_nstr"] = "".join("." if not x else ALPH[lst.index(x)] for x in nm_day)
        # the first and last day of the longest run of sea days (for the text): wrap round the year
        rec[f"{ev}_runs"] = int(((op != np.roll(op, 1)) & op).sum()) if 0 < op.sum() < 365 else (1 if op.all() else 0)
    rec["both_days"] = int((RAYS[b["id"]]["set"]["day_open"] & RAYS[b["id"]]["rise"]["day_open"]).sum())
    rows.append(rec)

C = [x for x in rows if x["status"] == "coast"]
n = len(C)
R = {"tiles": VER, "n": {"osm_pieces": 1826, "beaches": len(beaches), "coast": n, "inland": sum(1 for x in rows if x["status"] == "inland"),
                        "failed": sum(1 for x in rows if x["status"] == "failed"), "gb": sum(1 for x in C if x["cc"] == "GB"), "ie": sum(1 for x in C if x["cc"] == "IE")}}
ss = np.array([x["sea_set_days"] for x in C]); sr = np.array([x["sea_rise_days"] for x in C])
R["set"] = {"any": int((ss > 0).sum()), "any_pc": 100 * (ss > 0).mean(), "all_year": int((ss == 365).sum()), "all_year_pc": 100 * (ss == 365).mean(),
            "half": int((ss >= 183).sum()), "none": int((ss == 0).sum()), "mean_days": float(ss.mean()), "jun21": sum(x["set_jun21"] for x in C), "dec21": sum(x["set_dec21"] for x in C)}
R["rise"] = {"any": int((sr > 0).sum()), "any_pc": 100 * (sr > 0).mean(), "all_year": int((sr == 365).sum()), "all_year_pc": 100 * (sr == 365).mean(),
             "half": int((sr >= 183).sum()), "none": int((sr == 0).sum()), "mean_days": float(sr.mean()), "jun21": sum(x["rise_jun21"] for x in C), "dec21": sum(x["rise_dec21"] for x in C)}
both = [x for x in C if x["sea_set_days"] > 0 and x["sea_rise_days"] > 0]
R["both"] = {"n": len(both), "pc": 100 * len(both) / n, "same_day": sum(1 for x in C if x["both_days"] > 0), "same_day_all_year": sum(1 for x in C if x["both_days"] == 365)}
R["neither"] = sum(1 for x in C if x["sea_set_days"] == 0 and x["sea_rise_days"] == 0)
R["rise_only"] = sum(1 for x in C if x["sea_set_days"] == 0 and x["sea_rise_days"] > 0)
R["set_only"] = sum(1 for x in C if x["sea_set_days"] > 0 and x["sea_rise_days"] == 0)
for k in ("neither", "rise_only", "set_only"):
    R[k + "_pc"] = 100 * R[k] / n
# summer only, winter only
R["summer_only_set"] = sum(1 for x in C if x["set_jun21"] and not x["set_dec21"] and not x["set_mar20"])
R["winter_only_set"] = sum(1 for x in C if x["set_dec21"] and not x["set_jun21"] and not x["set_mar20"])
R["jun_not_dec_set"] = sum(1 for x in C if x["set_jun21"] and not x["set_dec21"])
R["dec_not_jun_set"] = sum(1 for x in C if x["set_dec21"] and not x["set_jun21"])
# by nation
R["nations"] = {}
for nat in ("England", "Scotland", "Wales", "Northern Ireland", "Ireland", "Isle of Man"):
    s = [x for x in C if x["nation"] == nat]
    if not s: continue
    R["nations"][nat] = {"n": len(s), "set_any_pc": 100 * np.mean([x["sea_set_days"] > 0 for x in s]), "rise_any_pc": 100 * np.mean([x["sea_rise_days"] > 0 for x in s]),
                         "set_all_pc": 100 * np.mean([x["sea_set_days"] == 365 for x in s]), "both_pc": 100 * np.mean([x["sea_set_days"] > 0 and x["sea_rise_days"] > 0 for x in s]),
                         "mean_set": float(np.mean([x["sea_set_days"] for x in s])), "mean_rise": float(np.mean([x["sea_rise_days"] for x in s]))}
# islands that block the Sun
isl = defaultdict(lambda: {"set_beaches": 0, "set_days": 0, "rise_beaches": 0, "rise_days": 0, "examples": []})
for x in C:
    for ev in ("set", "rise"):
        for nm, d in x[f"{ev}_islands"].items():
            I = isl[nm]; I[f"{ev}_beaches"] += 1; I[f"{ev}_days"] += d
            I["examples"].append((d, x["name"], ev, x["county"]))
IS = []
for nm, I in isl.items():
    ex = sorted(I["examples"], reverse=True)[:6]
    IS.append({"name": nm, "set_beaches": I["set_beaches"], "set_days": I["set_days"], "rise_beaches": I["rise_beaches"], "rise_days": I["rise_days"],
               "examples": [{"beach": e[1], "days": e[0], "event": e[2], "county": e[3]} for e in ex]})
IS.sort(key=lambda d: -(d["set_beaches"] + d["rise_beaches"]))
R["islands"] = IS[:30]
R["dup_island_names"] = {k: sorted(v) for k, v in DUP_ISLANDS.items()}
R["island_beaches_set"] = sum(1 for x in C if x["set_islands"])
R["island_beaches_rise"] = sum(1 for x in C if x["rise_islands"])
# tops
key = lambda x: (x["name"], x["county"], x["nation"])
R["top_both"] = [dict(name=x["name"], county=x["county"], nation=x["nation"], set=x["sea_set_days"], rise=x["sea_rise_days"], same=x["both_days"]) for x in
                 sorted(C, key=lambda x: -(x["both_days"] * 1000 + x["sea_set_days"] + x["sea_rise_days"]))[:15]]
CASES = [("Sennen Cove", "Cornwall"), ("Fistral Beach", "Cornwall"), ("Porthcurno", "Cornwall"), ("Longsands", "North Tyneside"), ("Troon", "South Ayrshire"),
         ("Woolacombe Sands", "Devon"), ("Croyde Beach", "Devon"), ("Fleswick Bay", "Cumbria"), ("Crosby Beach", "Sefton"), ("Half Moon Bay", "Lancashire"),
         ("Killiney Beach", None), ("Dollymount Strand", "Dublin"), ("Inch Beach", "Kerry"), ("Keem Beach", "Mayo"), ("Lahinch Beach", "Clare"),
         ("Gilpin Harbour", "Down"), ("Brighton Beach", "Brighton and Hove"), ("Rhossili Bay Beach", "Swansea"), ("Whitesands Beach", "Pembrokeshire"),
         ("Botany Bay", "Kent"), ("Saltburn Sands", "Redcar and Cleveland"), ("Durdle Door", "Dorset")]
R["cases"] = {}
for nm, cty in CASES:
    m = [x for x in C if x["name"] == nm and (cty is None or x["county"] == cty)]
    assert len(m) == 1, (nm, len(m))
    x = m[0]
    R["cases"][re.sub(r"\W+", "_", nm.lower()).strip("_")] = {k: x[k] for k in ("id", "name", "county", "nation", "sea_set_days", "sea_rise_days", "set_jun21", "set_dec21",
                                                                                 "rise_jun21", "rise_dec21", "set_islands", "rise_islands", "both_days", "set_block_med_km")}
R["all_year_set_counties"] = dict(Counter(x["county"] for x in C if x["sea_set_days"] == 365).most_common(6))
R["all_year_rise_counties"] = dict(Counter(x["county"] for x in C if x["sea_rise_days"] == 365).most_common(6))
iom = next((i for i in IS if i["name"] == "Isle of Man"), None); R["iom"] = iom
R["iow"] = next(i for i in IS if i["name"] == "Isle of Wight"); R["lundy"] = next(i for i in IS if i["name"] == "Lundy"); R["arran"] = next(i for i in IS if i["name"] == "Isle of Arran")
_tot = {i["name"]: i["set_beaches"] + i["rise_beaches"] for i in IS}
R["island_top_n"] = max(_tot.values()); R["island_top"] = sorted(k for k, v in _tot.items() if v == R["island_top_n"])
_bc = Counter(x["county"] for x in both).most_common(4)
R["both_counties"] = [{"county": k, "n": v} for k, v in _bc]
R["n_islands_named"] = sum(1 for i in IS if i["name"])
R["dec_vs_jun_set"] = R["set"]["dec21"] - R["set"]["jun21"]; R["dec_vs_jun_rise"] = R["rise"]["dec21"] - R["rise"]["jun21"]
DIP = math.sqrt(2 * EYE_M / R_EFF)
R["model"] = {"eye_m": EYE_M, "k": K_REFR, "near_km": NEAR_KM, "far_km": FAR_KM, "az_step": AZ_STEP, "mpx_m_50": 40075016.7 * math.cos(math.radians(50)) / (2 ** Z * MPX),
              "mpx_m_60": 40075016.7 * math.cos(math.radians(60)) / (2 ** Z * MPX), "dip_deg": math.degrees(DIP), "drop_20km_m": 20000 ** 2 / (2 * R_EFF),
              "hidden_50km_m": (50000 - math.sqrt(2 * EYE_M * R_EFF)) ** 2 / (2 * R_EFF)}
R["overall_set_coast_pc"] = 100 * sum(x["set_blockers"].get("coast", 0) for x in C) / max(1, sum(sum(x["set_blockers"].values()) for x in C))
jsave_rows = None
pickle.dump(rows, open(f"{SCR}/results_rows.pkl", "wb"))
jsave(R, f"{DATA}/results.json", indent=1, keepdash=True)
print(json.dumps({k: R[k] for k in ("n", "set", "rise", "both", "neither", "rise_only", "set_only", "nations")}, indent=0)[:3000])
print("islands", [(i["name"], i["set_beaches"], i["set_days"], i["rise_beaches"], i["rise_days"]) for i in IS[:25]])
