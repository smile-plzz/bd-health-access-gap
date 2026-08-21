"""Road-network accessibility: nearest-facility travel time per population point.

Builds the graph from raw Overpass JSON (see fetch_roads.py) rather than
via osmnx's graph_from_place/graph_from_bbox - those go through python's
requests library, which repeatedly failed to connect to Overpass hosts in
this environment even though curl reached them fine. Fetching with curl
and parsing here sidesteps that.
"""

import json
import math

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

# Default speed by highway type, km/h - rough defaults, not measured.
DEFAULT_SPEEDS_KPH = {
    "motorway": 80,
    "trunk": 60,
    "primary": 50,
    "secondary": 40,
    "tertiary": 30,
    "unclassified": 25,
    "residential": 20,
    "service": 15,
    "track": 10,
}
FALLBACK_SPEED_KPH = 20


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def build_road_graph_from_overpass_json(path: str) -> nx.Graph:
    """Parse an Overpass JSON road dump (nodes + ways with highway tags) into
    an undirected graph with 'length' (m) and 'travel_time' (s) edge weights.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    node_coords = {}
    ways = []
    for el in data["elements"]:
        if el["type"] == "node":
            node_coords[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way":
            ways.append(el)

    graph = nx.Graph()
    for way in ways:
        highway = way.get("tags", {}).get("highway", "unclassified")
        speed_kph = DEFAULT_SPEEDS_KPH.get(highway, FALLBACK_SPEED_KPH)
        node_ids = way["nodes"]
        for a, b in zip(node_ids[:-1], node_ids[1:]):
            if a not in node_coords or b not in node_coords:
                continue
            lat1, lon1 = node_coords[a]
            lat2, lon2 = node_coords[b]
            length_m = _haversine_m(lat1, lon1, lat2, lon2)
            travel_time_s = length_m / (speed_kph * 1000 / 3600)
            graph.add_node(a, lat=lat1, lon=lon1)
            graph.add_node(b, lat=lat2, lon=lon2)
            graph.add_edge(a, b, length=length_m, travel_time=travel_time_s, highway=highway)

    return graph


class NodeIndex:
    """KD-tree over graph node coordinates for fast nearest-node lookup."""

    def __init__(self, graph: nx.Graph):
        self.node_ids = list(graph.nodes)
        coords = np.array([(graph.nodes[n]["lat"], graph.nodes[n]["lon"]) for n in self.node_ids])
        self.tree = cKDTree(coords)

    def nearest(self, lat: float, lon: float) -> int:
        _, idx = self.tree.query([lat, lon])
        return self.node_ids[idx]


def nearest_facility_time(
    graph: nx.Graph,
    index: NodeIndex,
    origin_lat: float,
    origin_lon: float,
    facility_nodes: list[int],
) -> float:
    """Travel time (seconds) from an origin point to the nearest of a set of
    facility nodes, via single-source Dijkstra over the road graph.
    """
    origin_node = index.nearest(origin_lat, origin_lon)
    lengths = nx.single_source_dijkstra_path_length(graph, origin_node, weight="travel_time")
    times = [lengths[n] for n in facility_nodes if n in lengths]
    return min(times) if times else float("inf")
