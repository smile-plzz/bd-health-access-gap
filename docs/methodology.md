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

- Straight pairwise nearest-facility search in `access.py` is O(n) per origin — fine for a pilot district, needs a spatial index (e.g. `scipy.cKDTree` on graph nodes) before scaling nationally.
- OSM facility POIs (`amenity=hospital/clinic/doctors/pharmacy`) are crowd-tagged, not an official registry — coverage is uneven by region, and there's no facility-capacity/type detail beyond the tag. Good enough for a pilot; cross-check against DGHS's "Doctor Directory" dataset on data.gov.bd before drawing strong conclusions.
- Travel time via `drive` network may not reflect real access in areas dependent on walking/rickshaw/boat.
- In this dev environment, python's `requests`/urllib3 stack repeatedly failed to connect to Overpass API hosts while `curl` reached them fine — `src/fetch_facilities.py` shells out to curl for that reason. Worth retesting plain `requests` if this moves to a different machine/CI.
