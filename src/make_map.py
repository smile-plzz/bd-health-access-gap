"""Build an interactive choropleth map of a district's access-gap scores."""

import argparse

import folium
import geopandas as gpd

FACILITIES_PATH = "data/processed/facilities_with_upazila.geojson"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district", default="Kishoreganj", help="adm2_name to map")
    parser.add_argument(
        "--scores-path",
        default="data/processed/pilot_access_scores.geojson",
        help="output of score_pilot.py for this district",
    )
    parser.add_argument("--facilities-path", default=FACILITIES_PATH)
    parser.add_argument("--out", default=None, help="default: maps/<district_slug>_access_gap.html")
    args = parser.parse_args()

    out_path = args.out or f"maps/{args.district.lower().replace(' ', '_')}_access_gap.html"

    scores = gpd.read_file(args.scores_path)
    scores = scores[["adm3_name", "total_pop", "nearest_facility_min", "geometry"]]
    facilities = gpd.read_file(args.facilities_path)
    pilot_facilities = facilities[facilities["adm2_name"] == args.district]

    center = scores.geometry.union_all().centroid
    m = folium.Map(location=[center.y, center.x], zoom_start=10, tiles="cartodbpositron")

    folium.Choropleth(
        geo_data=scores.__geo_interface__,
        data=scores,
        columns=["adm3_name", "nearest_facility_min"],
        key_on="feature.properties.adm3_name",
        fill_color="YlOrRd",
        fill_opacity=0.75,
        line_opacity=0.5,
        legend_name="Travel time to nearest health facility (minutes)",
        nan_fill_color="lightgray",
    ).add_to(m)

    folium.GeoJson(
        scores.__geo_interface__,
        style_function=lambda _: {"fillOpacity": 0, "color": "transparent"},
        tooltip=folium.GeoJsonTooltip(
            fields=["adm3_name", "total_pop", "nearest_facility_min"],
            aliases=["Upazila", "Population", "Nearest facility (min)"],
        ),
    ).add_to(m)

    for _, row in pilot_facilities.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=2,
            color="#2b6cb0",
            fill=True,
            fill_opacity=0.8,
            popup=row.get("name") or row.get("amenity"),
        ).add_to(m)

    m.save(out_path)
    print(f"saved map to {out_path}")


if __name__ == "__main__":
    main()
