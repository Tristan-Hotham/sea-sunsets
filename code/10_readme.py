"""Step 10: README.md, LICENSE and reddit/post.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
N, C = R["n"], R["cases"]
rows = "\n".join(f"| {k} | {v['n']} | {v['set_any_pc']:.0f}% | {v['rise_any_pc']:.0f}% | {v['both_pc']:.0f}% | {v['mean_set']:.0f} | {v['mean_rise']:.0f} |" for k, v in R["nations"].items())
readme = f"""# Where the sun sets into the sea

Sea sunsets and sea sunrises through the year at the {N['coast']:,} named coastal beaches of the United Kingdom and Ireland in OpenStreetMap. From a point at the water's edge (eye {R['model']['eye_m']:.0f} m above the sea), rays every {R['model']['az_step']} degrees across the year's sunset and sunrise bearings, out to {R['model']['far_km']:.0f} km, over OpenStreetMap's coastline (OpenFreeMap tiles, release {R['tiles']}) and terrain, with the Earth's curve and refraction.

Interactive page: https://maps.tristanhotham.com/sea-sunsets/
Paper: {{https://doi.org/10.5281/zenodo.24089892}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/sea-sunsets/}}
Code and data: https://github.com/Tristan-Hotham/sea-sunsets

## Headline results

- {R['set']['any_pc']:.0f}% of beaches ({R['set']['any']}) see the Sun set into open sea on at least one day of 2026; {R['rise']['any_pc']:.0f}% ({R['rise']['any']}) see it rise out of the sea; {R['both']['n']} get both; {R['neither_pc']:.0f}% get neither.
- {R['set']['all_year']} beaches have a sea sunset every day, {R['all_year_set_counties']['Cornwall']} of them on the mainland coast of Cornwall (Sennen Cove among them); {R['rise']['all_year']} have a sea sunrise every day (Wexford {R['all_year_rise_counties']['Wexford']}, Wicklow {R['all_year_rise_counties']['Wicklow']}, East Riding of Yorkshire {R['all_year_rise_counties']['East Riding of Yorkshire']}; Longsands, Killiney).
- Winter is better: on 21 December {R['set']['dec21']} beaches have a sea sunset and {R['rise']['dec21']} a sea sunrise; on 21 June {R['set']['jun21']} and {R['rise']['jun21']}.
- Wales has the highest share of sea-sunset beaches ({R['nations']['Wales']['set_any_pc']:.0f}%).
- Islands: Arran hides the sunset from Troon on {C['troon']['set_islands']['Isle of Arran']} days; Lundy from Woolacombe on {C['woolacombe_sands']['set_islands']['Lundy']} and Croyde on {C['croyde_beach']['set_islands']['Lundy']}; the Isle of Man from Fleswick Bay on {C['fleswick_bay']['set_islands']['Isle of Man']} sunsets and the sunrise from County Down beaches on up to {C['gilpin_harbour']['rise_islands']['Isle of Man']} days; the Isle of Wight and Mull affect the most beaches ({R['island_top_n']} each).

| Nation | Beaches | Sea sunset | Sea sunrise | Both | Mean sunset days | Mean sunrise days |
|---|---|---|---|---|---|---|
{rows}

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page: MapLibre on OpenFreeMap Positron, beaches coloured by sea-sunset or sea-sunrise days or by the chosen day, date slider, the lines of sunset and sunrise from the chosen beach, a rose of the year's bearings. |
| `header.png` | Social card, 1200 x 630. |
| `data/beaches.csv` | Every beach ({N['beaches']:,}): name, OSM ids, observer point, county, nation, nearest UK town, sea sunset and sunrise days, solstice results, islands in the way, and day-by-day strings (two characters per day: `..` open sea, else the distance to the blocking land in 50 m units in base 62, digits `0-9A-Za-z`). |
| `data/beaches.json`, `data/site.json`, `data/area.geojson` | Page data. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts in order, templates, `qa.js`. |
| `release/` | Paper, blog post and figures, Zenodo files. |
| `reddit/` | Collage and post text. |

## Method in brief

- Beaches: OSM natural=beach with a name in GB and IE (QLever); pieces of the same name within 1 km merged; no sea within 600 m = inland, left out ({N['inland']}).
- Sea: OpenFreeMap zoom-10 tiles, water class ocean, rasterised at 1,024 px per tile (about 20 to 25 m) within {R['model']['near_km']:.0f} km; terrain above 0 m beyond (AWS Terrain Tiles z10).
- Observer: the sea pixel at least two pixels from land along the beach with the widest view over the year's arcs (first 3 km); eye {R['model']['eye_m']:.0f} m.
- Visibility: land blocks if (h - eye)/d - d/(2R') > -sqrt(2 eye/R'), R' = R/(1 - {R['model']['k']}).
- Sun: Spencer (1971) declination for each day of 2026; rise and set azimuth at apparent altitude -0.833 degrees minus the dip.
- Naming: own coast (same land mass within {R['model']['near_km']:.0f} km), mainland (Natural Earth polygon of 10,000 km2 or more) or island (named from OSM island places).

## How to rerun

Needs Python 3 with numpy, scipy, shapely 2, rasterio, mapbox-vector-tile, matplotlib, Pillow; xelatex; node with Playwright. Tiles and masks go to a scratch folder (`code/common.py`); tiles are deleted as soon as they are rasterised.

```
python3 code/01_beaches.py     # beaches, merging, tiles needed
python3 code/02_tiles.py       # OpenFreeMap tiles -> sea masks (network, about 36 MB fetched)
python3 code/03_rays.py        # observers, rays, days (about an hour)
python3 code/03b_landmass.py   # what is in the way: own coast, mainland or island
python3 code/04_results.py     # results.json
python3 code/05_export.py      # data files
python3 code/06_figures.py     # figures and header
python3 code/07_build_site.py  # index.html
python3 code/08_paper.py       # paper PDF (set DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py      # collage
python3 code/10_readme.py      # README, LICENSE, Reddit post
python3 code/09_release.py     # blog post, Zenodo files
```

## Sources and licences

- OpenStreetMap contributors (https://www.openstreetmap.org/copyright), ODbL, via QLever and OpenFreeMap (https://openfreemap.org/). Derived data are under the ODbL.
- AWS Terrain Tiles (https://registry.opendata.aws/terrain-tiles/). Natural Earth (public domain).
- Base map: OpenFreeMap Positron style. Fonts: MedievalSharp, IM Fell (SIL OFL).
- Text and figures CC BY 4.0; code MIT.

## Citation

Hotham, T. (2026) Where the sun sets into the sea: sea sunsets and sunrises at the beaches of Britain and Ireland. Zenodo. {{10.5281/zenodo.24089892}}

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = open("/home/claude/studies/renamed-world/LICENSE", encoding="utf-8").read().replace(
    "Derived data (data/): CC0 1.0, like its source, Wikidata.", "Derived data (data/): Open Database Licence (ODbL) 1.0, as derived from OpenStreetMap (c) OpenStreetMap contributors.")
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""**Title:** [OC] Where the sun sets into the sea: I traced the sunset and sunrise from {N['coast']:,} beaches in Britain and Ireland for every day of the year. Only {R['set']['all_year']} get a sea sunset every day

**Body:**

For every named beach in OpenStreetMap, rays from the water's edge along each day's sunset and sunrise bearing, over the coastline and terrain, with the Earth's curve and refraction (land far away hides below the horizon).

- {R['set']['any_pc']:.0f}% of beaches see the Sun set into open sea on some day of the year, {R['rise']['any_pc']:.0f}% see it rise out of the sea, {R['neither_pc']:.0f}% neither.
- {R['set']['all_year']} beaches get a sea sunset every single day, {R['all_year_set_counties']['Cornwall']} of them in Cornwall.
- Winter is better: {R['rise']['dec21']} beaches have a sea sunrise on 21 December, {R['rise']['jun21']} on 21 June.
- Wales is the sunset nation ({R['nations']['Wales']['set_any_pc']:.0f}% of beaches).
- Islands in the way: Arran takes {C['troon']['set_islands']['Isle of Arran']} sunsets a year from Troon, Lundy {C['woolacombe_sands']['set_islands']['Lundy']} from Woolacombe.

Interactive map (date slider, tap a beach for its year of sunsets): https://maps.tristanhotham.com/sea-sunsets/

**Source comment:**

Data: OpenStreetMap contributors (ODbL) via QLever and OpenFreeMap vector tiles; AWS Terrain Tiles; Natural Earth. Sun: NOAA/Spencer declination. Tools: Python (numpy, scipy, shapely, rasterio, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/sea-sunsets
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, post):
    for bad in ("—", "–", "DSIT", "DCMS"):
        assert bad not in t, bad
print("readme", len(readme.split()), "words")
