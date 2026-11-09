"""Step 5: data files. data/beaches.csv (every beach, reusable), data/beaches.json and data/site.json (page),
data/area.geojson (outline of the mapped area: Great Britain, Ireland, the Isle of Man and their islands)."""
import csv, pickle
import numpy as np
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from common import *

rows = pickle.load(open(f"{SCR}/results_rows.pkl", "rb"))
R = jload(f"{DATA}/results.json")
with open(f"{DATA}/beaches.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "name", "country", "status", "osm_ids", "surface", "lon", "lat", "obs_lon", "obs_lat", "county", "nation", "nearest_town", "town_km",
                "sea_sunset_days", "sea_sunrise_days", "both_same_day", "sunset_21jun_sea", "sunset_21dec_sea", "sunrise_21jun_sea", "sunrise_21dec_sea",
                "sunset_islands", "sunrise_islands", "sunset_by_day", "sunrise_by_day"])
    for x in rows:
        c = x["status"] == "coast"
        w.writerow([x["id"], x["name"], x["cc"], x["status"], " ".join(x["osm"]), x["surface"], round(x["lon"], 5), round(x["lat"], 5),
                    round(x["olon"], 5) if c else "", round(x["olat"], 5) if c else "", x.get("county", ""), x.get("nation", ""), x.get("town") or "", x.get("town_km") or "",
                    x.get("sea_set_days", ""), x.get("sea_rise_days", ""), x.get("both_days", ""), x.get("set_jun21", ""), x.get("set_dec21", ""),
                    x.get("rise_jun21", ""), x.get("rise_dec21", ""),
                    "; ".join(f"{k} ({v})" for k, v in sorted(x.get("set_islands", {}).items(), key=lambda t: -t[1])),
                    "; ".join(f"{k} ({v})" for k, v in sorted(x.get("rise_islands", {}).items(), key=lambda t: -t[1])),
                    x.get("_set_str", ""), x.get("_rise_str", "")])
page = []
for x in rows:
    if x["status"] != "coast": continue
    page.append({"id": x["id"], "n": x["name"], "olon": round(x["olon"], 5), "olat": round(x["olat"], 5), "ss": x["_set_str"], "rs": x["_rise_str"],
                 "sn": x["_set_nstr"], "rn": x["_rise_nstr"], "sN": x["_set_names"], "rN": x["_rise_names"], "town": x["town"], "county": x["county"],
                 "nat": x["nation"], "surf": x["surface"], "osm": x["osm"][:1]})
DIP = math.degrees(math.sqrt(2 * EYE_M / R_EFF))
jsave({"b": page}, f"{DATA}/beaches.json", keepdash=True)
jsave({"h0": H0 - DIP, "n": len(page)}, f"{DATA}/site.json")
ne = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
g = unary_union([shape(f["geometry"]) for f in ne if f["properties"]["ADM0_A3"] in ("GBR", "IRL", "IMN")]).simplify(0.01)
g = g.intersection(shape({"type": "Polygon", "coordinates": [[[-11, 49.5], [2.2, 49.5], [2.2, 61], [-11, 61], [-11, 49.5]]]}))
jsave({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": mapping(g)}]}, f"{DATA}/area.geojson")
print("page beaches", len(page), os.path.getsize(f"{DATA}/beaches.json") // 1024, "KB; area", os.path.getsize(f"{DATA}/area.geojson") // 1024, "KB")
