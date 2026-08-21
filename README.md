# BD Health Access Gap

Geospatial analysis of healthcare facility accessibility across Bangladesh, using open government data. Measures road-network travel time from population centers to nearest health facility, identifies underserved upazilas, and correlates access gaps with socioeconomic indicators.

## Goal

- **Tool**: compute real road-network distance/travel-time from each population point to nearest health facility (not straight-line)
- **Visualization**: interactive choropleth map of access gaps by upazila
- **Analysis**: correlate access gaps with poverty/literacy data, write up findings + policy implications

## Data sources

| Dataset | Source | Status |
|---|---|---|
| Health facility locations (DGHS) | data.gov.bd / DGHS | TODO: download |
| Population by upazila (BBS census) | data.gov.bd / BBS | TODO: download |
| Road network | OpenStreetMap (Bangladesh extract via OSMnx) | pulled at runtime |
| Administrative boundaries | data.gov.bd / GADM | TODO: download |

Raw files go in `data/raw/` (gitignored — large files). Cleaned/processed outputs go in `data/processed/`.

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

Skeleton stage. Next: pull DGHS facility list + BBS population data, geocode facilities, build OSM road graph for a pilot district.
