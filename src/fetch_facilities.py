"""Pull health facility POIs (hospitals, clinics, doctors, pharmacies) for
Bangladesh from OpenStreetMap via the Overpass API.

Uses curl as the transport rather than python's requests/urllib3 - in
testing, python's HTTPS stack repeatedly hit connect timeouts against
overpass-api.de from this environment while curl reached it immediately.
If that turns out to be environment-specific, swap _run_overpass_query
for a plain `requests.post` call.
"""

import argparse
import json
import subprocess

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

QUERY_TEMPLATE = (
    '[out:json][timeout:300];'
    'area["ISO3166-1"="BD"][admin_level=2]->.a;'
    '(node["amenity"~"hospital|clinic|doctors|pharmacy"](area.a);'
    'way["amenity"~"hospital|clinic|doctors|pharmacy"](area.a););'
    'out center tags;'
)


def _run_overpass_query(query: str, timeout: int = 320) -> dict:
    result = subprocess.run(
        ["curl", "-s", "-m", str(timeout), "-X", "POST", "-d", query, OVERPASS_URL],
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def _elements_to_geojson(elements: list[dict]) -> dict:
    features = []
    for el in elements:
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        else:
            center = el.get("center")
            if not center:
                continue
            lat, lon = center["lat"], center["lon"]
        tags = el.get("tags", {})
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "osm_id": el["id"],
                    "osm_type": el["type"],
                    "amenity": tags.get("amenity"),
                    "name": tags.get("name"),
                    "addr_city": tags.get("addr:city"),
                    "addr_district": tags.get("addr:district"),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def fetch_bangladesh_facilities() -> dict:
    data = _run_overpass_query(QUERY_TEMPLATE)
    return _elements_to_geojson(data["elements"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/raw/osm_health_facilities.geojson")
    args = parser.parse_args()

    geojson = fetch_bangladesh_facilities()
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(geojson, f)
    print(f"fetched {len(geojson['features'])} facilities, saved to {args.out}")
