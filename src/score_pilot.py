"""Pilot accessibility scoring for Kishoreganj district.

For each upazila in the pilot district, computes road-network travel time
from the upazila centroid to the nearest health facility, and writes a
scored GeoJSON + summary CSV to data/processed/.
"""

import geopandas as gpd
import networkx as nx
import pandas as pd

from access import NodeIndex, build_road_graph_from_overpass_json

ROADS_PATH = "data/raw/kishoreganj_roads.json"
UPAZILA_PATH = "data/processed/upazila_population.geojson"
FACILITIES_PATH = "data/processed/facilities_with_upazila.geojson"
PILOT_DISTRICT = "Kishoreganj"

OUT_GEOJSON = "data/processed/pilot_access_scores.geojson"
OUT_CSV = "data/processed/pilot_access_scores.csv"


def main() -> None:
    print("building road graph...")
    graph = build_road_graph_from_overpass_json(ROADS_PATH)
    print(f"graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    index = NodeIndex(graph)

    upazila = gpd.read_file(UPAZILA_PATH)
    pilot = upazila[upazila["adm2_name"] == PILOT_DISTRICT].copy()

    facilities = gpd.read_file(FACILITIES_PATH)
    pilot_facilities = facilities[facilities["adm2_name"] == PILOT_DISTRICT]
    facility_nodes = [index.nearest(pt.y, pt.x) for pt in pilot_facilities.geometry]
    print(f"pilot upazilas: {len(pilot)}, pilot facilities: {len(pilot_facilities)}")

    centroids = pilot.geometry.centroid
    travel_times_s = []
    for pt in centroids:
        origin_node = index.nearest(pt.y, pt.x)
        lengths = nx.single_source_dijkstra_path_length(graph, origin_node, weight="travel_time")
        times = [lengths[n] for n in facility_nodes if n in lengths]
        travel_times_s.append(min(times) if times else float("nan"))

    pilot["nearest_facility_min"] = [t / 60 if t == t else None for t in travel_times_s]
    pilot.to_file(OUT_GEOJSON, driver="GeoJSON")

    summary = pd.DataFrame(
        {
            "upazila": pilot["adm3_name"],
            "total_pop": pilot["total_pop"],
            "nearest_facility_min": pilot["nearest_facility_min"],
        }
    ).sort_values("nearest_facility_min", ascending=False)
    summary.to_csv(OUT_CSV, index=False)

    print(summary.to_string(index=False))
    print(f"wrote {OUT_GEOJSON} and {OUT_CSV}")


if __name__ == "__main__":
    main()
