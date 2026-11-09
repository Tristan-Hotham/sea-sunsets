# sea-sunsets: working notes

Brief: /home/claude/work/new10/BRIEFS.md (study 6) + shared rules. Format refs: tower-shadows (MapLibre/Positron), river-names.
Scratch: /home/claude/scratch/sea-sunsets (masks ~100 MB, rays.pkl) - deleted at the end; rerun 01..03b to rebuild (~1.5 h).

## Pipeline
- 01_beaches.py: 1,826 OSM pieces -> 1,768 beaches (same name, same country, within 1 km).
- 02_tiles.py: OFM planet 20261101_080013_pt, z10, 779 tiles within 12 km of a beach (36 MB fetched), each rasterised
  (water class ocean, 1024 px/tile, ~20-25 m) and deleted at once; island/islet place names kept.
- 03_rays.py: observer = best of up to 12 sea pixels (2 px clear of land) along the beach, judged by open bearings in the
  first 3 km; rays every 0.25 deg over the year's arcs; vector sea to 12 km (20 m steps), terrain z10 beyond (150 m steps)
  to 150 km; land blocks if elevation angle > -dip, eye 3 m, k = 0.13; near land min 5 m. Spencer declination, 2026.
- 03b_landmass.py: blocker = own coast (same connected land in the mask within 12 km) / mainland (NE polygon >= 10,000 km2)
  / island (NE polygon name from nearest OSM island place to its middle; small islands: nearest place within 4 km).
  Hand fixes: Jura (polygon's nearest place was the islet Eilean Ard), Isle of Man (no island place in tiles).
- 04_results.py, 05_export.py (day strings: 2 chars/day, base-62 distance in 50 m units; first version used 1-char log
  bins which drew rays short of Arran on the map, fixed), 06_figures.py, 07..10.
- 51 beaches inland (lake/river; 22 of them have no sea at all within 13 km).

## Checks by eye (rays drawn over the mask)
- Sennen Cove 365 sea sunsets; Fistral 304, not at midwinter (own headland); Longsands and Killiney 365 sea sunrises;
  Dollymount 183 rises (Howth); Keem Bay 0/0 (cove opens SE under cliffs: checked on the mask); Inch (Kerry) 94 (Dingle Bay);
  Troon: Arran 134 days; Woolacombe: Lundy 26 days (Lundy due west ~32 km); Croyde 28; Fleswick Bay: IoM 44.
- All-year sea-sunset beaches: 43 in Cornwall, none on Scilly (other islands in the way).
- Blackpool (Lancs) has no named beach in the data; "Blackpool" in the data is Blackpool Mill, Devon.
- NE admin-1 typo "North Ayshire" corrected; en dash in "Dun Laoghaire-Rathdown" replaced by a hyphen.

## Caveats
- Clear sky only; MHW coastline (low tide sands count as sea); refraction varies; best point on the beach; named beaches only;
  terrain z10 beyond 12 km can smear coast; far land outside the terrain box (south of 49.6 N, east of 2.1 E) not modelled.

## References to verify
- Spencer, J. W. (1971) Fourier series representation of the position of the sun. Search 2(5), 172.
- Bast & Buchhold (2017) QLever, CIKM 647-656.

## Independent review (2026)
- Pipeline rerun from raw (01 to 09): every headline number reproduced exactly.
- Sun azimuths checked against ephem (London 21 Jun set 311.1 vs 311.5; 21 Dec 231.7 vs 232.1).
- Rays drawn over the mask by eye: Sennen, Troon, Woolacombe, Croyde, Fleswick Bay, Crook Ness, Whitby West Cliff, Keem, Lahinch, Mannin Bay, Popplestones, Periglis.
- Scilly: no all-year sea sunsets is real (Gweal, Annet, Mincarlo, Illiswilgig and neighbouring islands stand in every west view).
- Fixes: 6 Dún Laoghaire-Rathdown beaches had no nation (Ireland n 429 -> 435); own-island specks named as other islands
  (Inishbofin, St Agnes) now count as own coast; the two Inishbofins (and Mainland, Horse Island) told apart by county;
  Isle of Wight ties with Mull (31 beaches each); "both" beaches are mostly Clacton/Kent, not headlands; Half Moon Bay is
  blocked in summer, not winter; scope is UK and Ireland (no Isle of Man beaches); Zenodo "degrees{}"; Clyde labels moved onto the sea.
