"""Pull health facility POIs (hospitals, clinics, doctors) for Bangladesh from OpenStreetMap."""

import geopandas as gpd
import osmnx as ox

TAGS = {"amenity": ["hospital", "clinic", "doctors", "pharmacy"]}


def fetch_bangladesh_facilities() -> gpd.GeoDataFrame:
    gdf = ox.features_from_place("Bangladesh", tags=TAGS)
    keep_cols = [c for c in ["name", "amenity", "geometry", "addr:city", "addr:district"] if c in gdf.columns]
    return gdf[keep_cols]


if __name__ == "__main__":
    facilities = fetch_bangladesh_facilities()
    print(f"fetched {len(facilities)} facilities")
    out_path = "data/raw/osm_health_facilities.geojson"
    facilities.to_file(out_path, driver="GeoJSON")
    print(f"saved to {out_path}")
