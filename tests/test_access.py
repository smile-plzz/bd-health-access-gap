import json
import math

import pytest

from access import (
    NodeIndex,
    _haversine_m,
    build_road_graph_from_overpass_json,
    nearest_facility_time,
)


def test_haversine_known_distance():
    # Dhaka to Chittagong, roughly 210-220km great-circle.
    d = _haversine_m(23.8103, 90.4125, 22.3569, 91.7832)
    assert 210_000 < d < 220_000


def test_haversine_zero_for_same_point():
    assert _haversine_m(23.0, 90.0, 23.0, 90.0) == 0


@pytest.fixture
def overpass_dump(tmp_path):
    # A simple line of 3 nodes joined by a residential way, plus a
    # disconnected node with no ways touching it.
    data = {
        "elements": [
            {"type": "node", "id": 1, "lat": 24.0, "lon": 90.0},
            {"type": "node", "id": 2, "lat": 24.01, "lon": 90.0},
            {"type": "node", "id": 3, "lat": 24.02, "lon": 90.0},
            {"type": "node", "id": 4, "lat": 25.0, "lon": 91.0},
            {
                "type": "way",
                "id": 100,
                "nodes": [1, 2, 3],
                "tags": {"highway": "residential"},
            },
        ]
    }
    path = tmp_path / "roads.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_build_road_graph_from_overpass_json(overpass_dump):
    graph = build_road_graph_from_overpass_json(overpass_dump)
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 2
    assert graph.has_edge(1, 2)
    assert graph.has_edge(2, 3)
    assert not graph.has_edge(1, 3)
    edge = graph.edges[1, 2]
    assert edge["travel_time"] == pytest.approx(edge["length"] / (20 * 1000 / 3600))


def test_node_index_nearest_returns_closest_node(overpass_dump):
    graph = build_road_graph_from_overpass_json(overpass_dump)
    index = NodeIndex(graph)
    assert index.nearest(24.001, 90.0) == 1
    assert index.nearest(24.019, 90.0) == 3


def test_nearest_facility_time_picks_minimum_over_candidates(overpass_dump):
    graph = build_road_graph_from_overpass_json(overpass_dump)
    index = NodeIndex(graph)
    # Facility at node 3 (far end) and node 2 (closer) - should pick node 2's time.
    t = nearest_facility_time(graph, index, 24.0, 90.0, facility_nodes=[2, 3])
    expected = graph.edges[1, 2]["travel_time"]
    assert t == pytest.approx(expected)


def test_nearest_facility_time_infinite_when_unreachable(overpass_dump):
    graph = build_road_graph_from_overpass_json(overpass_dump)
    index = NodeIndex(graph)
    t = nearest_facility_time(graph, index, 24.0, 90.0, facility_nodes=[999])
    assert math.isinf(t)
