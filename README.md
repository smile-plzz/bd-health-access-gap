# BD Health Access Gap

Geospatial analysis of healthcare facility accessibility across Bangladesh, using open government data. Measures road-network travel time from population centers to nearest health facility, identifies underserved upazilas, and correlates access gaps with socioeconomic indicators.

## Goal

- **Tool**: compute real road-network distance/travel-time from each population point to nearest health facility (not straight-line)
- **Visualization**: interactive choropleth map of access gaps by upazila
- **Analysis**: correlate access gaps with poverty/literacy data, write up findings + policy implications

## Data sources

| Dataset | Source | Status |
|---|---|---|
| Health facility locations (hospital/clinic/doctors/pharmacy POIs, n=7473) | OpenStreetMap via Overpass API — `src/fetch_facilities.py` | done — `data/raw/osm_health_facilities.geojson` |
| Population by upazila, 2022, age/sex-disaggregated | HDX `cod-ps-bgd` (`bgd_admpop_adm3_2022.csv`) | done |
| Administrative boundaries (upazila polygons, pcode-matched to population) | HDX `cod-ab-bgd` (`bgd_admin_boundaries.geojson.zip` → `bgd_admin3.geojson`) | done |
| Road network | OpenStreetMap (pulled per-district at analysis time via OSMnx) | pulled at runtime, not stored |

data.gov.bd's own health/population datasets turned out too thin for this (no coordinate data, population only as a scanned PDF report) — HDX's Common Operational Datasets and OSM directly filled the gap instead.

Raw files go in `data/raw/` (gitignored — large files, reproducible via source or `src/fetch_facilities.py`). Cleaned/processed outputs go in `data/processed/`.

## Stack

Python: pandas, geopandas, osmnx, networkx, folium, jupyter. See `requirements.txt`.

## Project structure

```
data/raw/         # untouched downloads
data/processed/   # cleaned, geocoded, joined datasets
notebooks/        # exploratory analysis, numbered by stage
src/              # reusable functions (geocoding, network analysis, scoring)
maps/             # exported map HTML/images
docs/             # writeup, methodology notes, findings
```

## Status

Pilot complete for Kishoreganj district (13 upazilas): data joined, road-network graph built, nearest-facility travel time computed per upazila, choropleth map rendered, findings written up. See `docs/findings.md` for results and `maps/kishoreganj_access_gap.html` for the interactive map.

**Pipeline, in order:**
1. `src/fetch_facilities.py` — pull health facility POIs from OSM (already run, output in `data/raw/`)
2. `src/join_data.py` — join population to boundaries, spatial-join facilities to upazilas → `data/processed/`
3. `src/access.py` + `src/score_pilot.py` — build road graph from an Overpass road dump, score nearest-facility travel time per upazila
4. `src/make_map.py` — render the choropleth

`score_pilot.py` and `make_map.py` now take `--district` (plus `--roads-path`/`--out`), so scoring a
second district no longer means editing hardcoded constants — running with no args reproduces the
Kishoreganj pilot outputs exactly. `join_data.py`'s population-to-boundary join now normalizes away
admin-suffix/punctuation differences and falls back to a within-district fuzzy match, raising the
match rate above the original 63% exact-name-join baseline (see `docs/methodology.md`). Run `pytest`
for unit tests covering the name-matching and road-graph logic.

**Next:** pull an Overpass road dump for a second district and run the now-generalized scoring
pipeline against it (this environment currently can't reach Overpass/HDX, so that's untested end to
end here), get a real ADM3 pcode crosswalk to replace the fuzzy name join, cross-check OSM facility
coverage against DGHS's own directory, correlate access scores with a poverty/literacy indicator.
