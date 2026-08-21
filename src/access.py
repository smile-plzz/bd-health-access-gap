"""Road-network accessibility: nearest-facility travel time per population point."""

import geopandas as gpd
import networkx as nx
import osmnx as ox


def build_road_graph(place: str = "Dhaka, Bangladesh", network_type: str = "drive") -> nx.MultiDiGraph:
    """Pull an OSM road network graph for a place, with travel-time edge weights."""
    graph = ox.graph_from_place(place, network_type=network_type)
    graph = ox.add_edge_speeds(graph)
    graph = ox.add_edge_travel_times(graph)
    return graph


def nearest_facility_time(
    graph: nx.MultiDiGraph,
    origin_lat: float,
    origin_lon: float,
    facilities: gpd.GeoDataFrame,
) -> float:
    """Travel time (seconds) from an origin point to the nearest facility via the road graph."""
    origin_node = ox.nearest_nodes(graph, origin_lon, origin_lat)
    best_time = float("inf")
    for _, facility in facilities.iterrows():
        dest_node = ox.nearest_nodes(graph, facility.geometry.x, facility.geometry.y)
        try:
            travel_time = nx.shortest_path_length(graph, origin_node, dest_node, weight="travel_time")
        except nx.NetworkXNoPath:
            continue
        best_time = min(best_time, travel_time)
    return best_time
