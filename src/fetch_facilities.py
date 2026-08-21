"""Pull health facility POIs (hospitals, clinics, doctors) from OpenStreetMap.

Country-wide queries against Bangladesh are large (auto-split into many
sub-queries by osmnx) and slow/fragile against the default Overpass
instance. Default here to a single pilot place; pass --country to attempt
the full-country pull once the pilot is validated.
"""

import argparse

import geopandas as gpd
import osmnx as ox

TAGS = {"amenity": ["hospital", "clinic", "doctors", "pharmacy"]}

# Public Overpass mirrors to fall back through if the default times out.
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]


def fetch_facilities(place: str) -> gpd.GeoDataFrame:
    last_error = None
    for mirror in OVERPASS_MIRRORS:
        ox.settings.overpass_url = mirror
        ox.settings.overpass_rate_limit = True
        ox.settings.requests_timeout = 180
        try:
            gdf = ox.features_from_place(place, tags=TAGS)
            break
        except Exception as exc:  # noqa: BLE001 - try next mirror
            last_error = exc
            continue
    else:
        raise RuntimeError(f"all Overpass mirrors failed for '{place}'") from last_error

    keep_cols = [c for c in ["name", "amenity", "geometry", "addr:city", "addr:district"] if c in gdf.columns]
    return gdf[keep_cols]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--place", default="Dhaka District, Bangladesh", help="pilot area (default: Dhaka District)")
    parser.add_argument("--country", action="store_true", help="fetch all of Bangladesh instead of the pilot place")
    parser.add_argument("--out", default=None, help="output GeoJSON path")
    args = parser.parse_args()

    place = "Bangladesh" if args.country else args.place
    out_path = args.out or f"data/raw/osm_health_facilities_{'bd' if args.country else 'pilot'}.geojson"

    facilities = fetch_facilities(place)
    print(f"fetched {len(facilities)} facilities for '{place}'")
    facilities.to_file(out_path, driver="GeoJSON")
    print(f"saved to {out_path}")
