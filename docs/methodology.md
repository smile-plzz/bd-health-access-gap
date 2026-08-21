# Methodology (draft)

## Question

Which upazilas in Bangladesh have the worst road-network access to health facilities, and does that gap correlate with poverty/literacy?

## Steps

1. **Collect** — DGHS facility list, BBS population by upazila, admin boundaries, OSM road network.
2. **Geocode** — resolve facility addresses/names to coordinates where missing (`src/geocode.py`).
3. **Network build** — pull OSM drive-network graph per division/district (`src/access.py`), pilot on one district first before scaling nationally (OSM graphs for full country are large).
4. **Accessibility scoring** — for each upazila centroid (or population-weighted point), compute travel time to nearest facility.
5. **Correlate** — join access scores with poverty/literacy indicators, look for underserved clusters.
6. **Visualize** — choropleth map of access-gap score by upazila (folium).
7. **Write up** — findings + policy implications in `docs/findings.md`.

## Known limitations to address later

- ~~Straight pairwise nearest-facility search in `access.py` is O(n) per origin~~ — `access.py`'s `NodeIndex` now uses `scipy.cKDTree` for nearest-node lookup, so this is resolved for graph-node search. Still open: nationally, per-district road graphs would need to be built for every district (`score_pilot.py` now takes `--district`/`--roads-path` so this is a matter of fetching more Overpass road dumps and running it repeatedly, not a code change) rather than one national graph, to keep each Dijkstra run's graph size manageable.
- The population-to-boundary name join (`src/join_data.py`) now normalizes admin suffixes/punctuation and falls back to a within-district fuzzy match (`difflib.get_close_matches`, cutoff 0.82) on top of the original exact join, raising the match rate above the original 63% (338/507) exact-name baseline — see `tests/test_join_data.py` for the matching behavior. This is still a heuristic name join, not a real pcode crosswalk; get an authoritative ADM3 pcode mapping between the two datasets' schemes before treating unmatched/fuzzy-matched upazilas as settled.
- OSM facility POIs (`amenity=hospital/clinic/doctors/pharmacy`) are crowd-tagged, not an official registry — coverage is uneven by region, and there's no facility-capacity/type detail beyond the tag. Good enough for a pilot; cross-check against DGHS's "Doctor Directory" dataset on data.gov.bd before drawing strong conclusions.
- Travel time via `drive` network may not reflect real access in areas dependent on walking/rickshaw/boat.
- In this dev environment, python's `requests`/urllib3 stack repeatedly failed to connect to Overpass API hosts while `curl` reached them fine — `src/fetch_facilities.py` shells out to curl for that reason. Worth retesting plain `requests` if this moves to a different machine/CI. (Also true of the sandboxed environment these tests were developed in — neither Overpass nor HDX were reachable at all, so the generalized `score_pilot.py`/`join_data.py` changes are unit-tested against synthetic fixtures but not re-run end to end against real data.)
