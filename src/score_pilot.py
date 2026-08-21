"""Accessibility scoring for a single district.

For each upazila in the given district, computes road-network travel time
from the upazila centroid to the nearest health facility, and writes a
scored GeoJSON + summary CSV to data/processed/.

Kishoreganj was the original pilot; this now takes --district and
--roads-path so the same scoring step can be run against any district that
has a road-network dump in data/raw/, one district at a time (see
docs/methodology.md for why a per-district road graph, rather than a
national one, is still the right unit of work here).
"""

import argparse
import re

import geopandas as gpd
import networkx as nx
import pandas as pd

from access import NodeIndex, build_road_graph_from_overpass_json

UPAZILA_PATH = "data/processed/upazila_population.geojson"
FACILITIES_PATH = "data/processed/facilities_with_upazila.geojson"


def _slug(district: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", district.lower()).strip("_")


def score_district(
    district: str,
    roads_path: str,
    upazila_path: str = UPAZILA_PATH,
    facilities_path: str = FACILITIES_PATH,
) -> pd.DataFrame:
    print(f"[{district}] building road graph from {roads_path}...")
    graph = build_road_graph_from_overpass_json(roads_path)
    print(f"[{district}] graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    index = NodeIndex(graph)

    upazila = gpd.read_file(upazila_path)
    district_upazila = upazila[upazila["adm2_name"] == district].copy()
    if district_upazila.empty:
        raise ValueError(f"no upazilas found for district {district!r} in {upazila_path}")

    facilities = gpd.read_file(facilities_path)
    district_facilities = facilities[facilities["adm2_name"] == district]
    facility_nodes = [index.nearest(pt.y, pt.x) for pt in district_facilities.geometry]
    print(f"[{district}] upazilas: {len(district_upazila)}, facilities: {len(district_facilities)}")

    # Bangladesh UTM zone 46N - project before centroid for an accurate result,
    # then convert back to lat/lon for the road-graph lookup.
    centroids = district_upazila.geometry.to_crs("EPSG:32646").centroid.to_crs("EPSG:4326")
    travel_times_s = []
    for pt in centroids:
        origin_node = index.nearest(pt.y, pt.x)
        lengths = nx.single_source_dijkstra_path_length(graph, origin_node, weight="travel_time")
        times = [lengths[n] for n in facility_nodes if n in lengths]
        travel_times_s.append(min(times) if times else float("nan"))

    district_upazila["nearest_facility_min"] = [t / 60 if t == t else None for t in travel_times_s]
    return district_upazila


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district", default="Kishoreganj", help="adm2_name to score")
    parser.add_argument(
        "--roads-path",
        default=None,
        help="Overpass road-dump JSON for this district (default: data/raw/<district_slug>_roads.json)",
    )
    parser.add_argument("--upazila-path", default=UPAZILA_PATH)
    parser.add_argument("--facilities-path", default=FACILITIES_PATH)
    parser.add_argument("--out-prefix", default=None, help="output path prefix (default: data/processed/<district_slug>)")
    args = parser.parse_args()

    slug = _slug(args.district)
    roads_path = args.roads_path or f"data/raw/{slug}_roads.json"
    # Keep the original pilot's output paths stable when run with defaults;
    # any other district gets a slug-based prefix.
    default_out_prefix = "data/processed/pilot_access_scores" if args.district == "Kishoreganj" else f"data/processed/{slug}_access_scores"
    out_prefix = args.out_prefix or default_out_prefix

    scored = score_district(args.district, roads_path, args.upazila_path, args.facilities_path)
    scored.to_file(f"{out_prefix}.geojson", driver="GeoJSON")

    summary = pd.DataFrame(
        {
            "upazila": scored["adm3_name"],
            "total_pop": scored["total_pop"],
            "nearest_facility_min": scored["nearest_facility_min"],
        }
    ).sort_values("nearest_facility_min", ascending=False)
    summary.to_csv(f"{out_prefix}.csv", index=False)

    print(summary.to_string(index=False))
    print(f"wrote {out_prefix}.geojson and {out_prefix}.csv")


if __name__ == "__main__":
    main()
