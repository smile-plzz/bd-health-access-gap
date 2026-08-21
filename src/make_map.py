"""Build an interactive choropleth map of pilot access-gap scores."""

import folium
import geopandas as gpd

SCORES_PATH = "data/processed/pilot_access_scores.geojson"
FACILITIES_PATH = "data/processed/facilities_with_upazila.geojson"
PILOT_DISTRICT = "Kishoreganj"
OUT_PATH = "maps/kishoreganj_access_gap.html"


def main() -> None:
    scores = gpd.read_file(SCORES_PATH)
    scores = scores[["adm3_name", "total_pop", "nearest_facility_min", "geometry"]]
    facilities = gpd.read_file(FACILITIES_PATH)
    pilot_facilities = facilities[facilities["adm2_name"] == PILOT_DISTRICT]

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

    m.save(OUT_PATH)
    print(f"saved map to {OUT_PATH}")


if __name__ == "__main__":
    main()
