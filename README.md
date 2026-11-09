# Where the sun sets into the sea

Sea sunsets and sea sunrises through the year at the 1,717 named coastal beaches of the United Kingdom and Ireland in OpenStreetMap. From a point at the water's edge (eye 3 m above the sea), rays every 0.25 degrees across the year's sunset and sunrise bearings, out to 150 km, over OpenStreetMap's coastline (OpenFreeMap tiles, release 20261101_080013_pt) and terrain, with the Earth's curve and refraction.

Interactive page: https://maps.tristanhotham.com/sea-sunsets/
Paper: https://doi.org/10.5281/zenodo.24089892
Blog post: https://blog.tristanhotham.com/2026/10/31/sea-sunsets/
Code and data: https://github.com/Tristan-Hotham/sea-sunsets

## Headline results

- 47% of beaches (805) see the Sun set into open sea on at least one day of 2026; 41% (703) see it rise out of the sea; 152 get both; 21% get neither.
- 52 beaches have a sea sunset every day, 43 of them on the mainland coast of Cornwall (Sennen Cove among them); 75 have a sea sunrise every day (Wexford 15, Wicklow 14, East Riding of Yorkshire 10; Longsands, Killiney).
- Winter is better: on 21 December 349 beaches have a sea sunset and 405 a sea sunrise; on 21 June 303 and 231.
- Wales has the highest share of sea-sunset beaches (67%).
- Islands: Arran hides the sunset from Troon on 134 days; Lundy from Woolacombe on 26 and Croyde on 28; the Isle of Man from Fleswick Bay on 44 sunsets and the sunrise from County Down beaches on up to 73 days; the Isle of Wight and Mull affect the most beaches (31 each).

| Nation | Beaches | Sea sunset | Sea sunrise | Both | Mean sunset days | Mean sunrise days |
|---|---|---|---|---|---|---|
| England | 608 | 48% | 56% | 14% | 84 | 115 |
| Scotland | 450 | 44% | 33% | 6% | 58 | 42 |
| Wales | 203 | 67% | 23% | 7% | 123 | 24 |
| Northern Ireland | 21 | 33% | 57% | 5% | 35 | 58 |
| Ireland | 435 | 38% | 35% | 6% | 34 | 63 |

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page: MapLibre on OpenFreeMap Positron, beaches coloured by sea-sunset or sea-sunrise days or by the chosen day, date slider, the lines of sunset and sunrise from the chosen beach, a rose of the year's bearings. |
| `header.png` | Social card, 1200 x 630. |
| `data/beaches.csv` | Every beach (1,768): name, OSM ids, observer point, county, nation, nearest UK town, sea sunset and sunrise days, solstice results, islands in the way, and day-by-day strings (two characters per day: `..` open sea, else the distance to the blocking land in 50 m units in base 62, digits `0-9A-Za-z`). |
| `data/beaches.json`, `data/site.json`, `data/area.geojson` | Page data. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts in order, templates, `qa.js`. |
| `release/` | Paper, blog post and figures, Zenodo files. |
| `reddit/` | Collage and post text. |

## Method in brief

- Beaches: OSM natural=beach with a name in GB and IE (QLever); pieces of the same name within 1 km merged; no sea within 600 m = inland, left out (51).
- Sea: OpenFreeMap zoom-10 tiles, water class ocean, rasterised at 1,024 px per tile (about 20 to 25 m) within 12 km; terrain above 0 m beyond (AWS Terrain Tiles z10).
- Observer: the sea pixel at least two pixels from land along the beach with the widest view over the year's arcs (first 3 km); eye 3 m.
- Visibility: land blocks if (h - eye)/d - d/(2R') > -sqrt(2 eye/R'), R' = R/(1 - 0.13).
- Sun: Spencer (1971) declination for each day of 2026; rise and set azimuth at apparent altitude -0.833 degrees minus the dip.
- Naming: own coast (same land mass within 12 km), mainland (Natural Earth polygon of 10,000 km2 or more) or island (named from OSM island places).

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

Hotham, T. (2026) Where the sun sets into the sea: sea sunsets and sunrises at the beaches of Britain and Ireland. Zenodo. 10.5281/zenodo.24089892

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
