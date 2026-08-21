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

Data collected: facilities, population, and admin boundaries all in `data/raw/`. Next: join population to boundary polygons, build OSM road graph for a pilot district, compute nearest-facility travel time (`src/access.py`), start `notebooks/01_explore_data.ipynb`.
