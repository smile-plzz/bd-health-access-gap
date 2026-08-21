"""Join upazila population to admin boundaries, and spatially join facilities
into their containing upazila. Writes the combined dataset to data/processed/.
"""

import json

import geopandas as gpd
import pandas as pd

BOUNDARIES_PATH = "data/raw/bgd_admin_boundaries/bgd_admin3.geojson"
POPULATION_PATH = "data/raw/bgd_admpop_adm3_2022.csv"
FACILITIES_PATH = "data/raw/osm_health_facilities.geojson"

OUT_UPAZILA_PATH = "data/processed/upazila_population.geojson"
OUT_FACILITIES_PATH = "data/processed/facilities_with_upazila.geojson"


def load_upazila_population() -> gpd.GeoDataFrame:
    """Join population to boundaries by (district, upazila) name.

    The population CSV (older census pcode scheme, 544 units) and the
    boundary file (newer COD-AB v03 pcode scheme, 507 units) use
    incompatible ADM3_PCODE formats, so pcode join is not possible here.
    Name join covers ~63% of upazilas (338/507) - the rest differ due to
    spelling variants and city-corporation units that don't split the
    same way across the two datasets. Good enough for a pilot; revisit
    with a proper pcode crosswalk before scaling nationally.
    """
    boundaries = gpd.read_file(BOUNDARIES_PATH)
    boundaries["_join_key"] = (
        boundaries["adm2_name"].str.lower().str.strip() + "|" + boundaries["adm3_name"].str.lower().str.strip()
    )

    population = pd.read_csv(POPULATION_PATH, encoding="utf-8-sig")
    population["_join_key"] = (
        population["ADM2_NAME"].str.lower().str.strip() + "|" + population["ADM3_NAME"].str.lower().str.strip()
    )

    pop_cols = ["_join_key", "F_TL", "M_TL", "T_TL"]
    merged = boundaries.merge(population[pop_cols], on="_join_key", how="left")
    merged = merged.rename(columns={"F_TL": "female_pop", "M_TL": "male_pop", "T_TL": "total_pop"})
    merged = merged.drop(columns=["_join_key"])
    return merged


def join_facilities_to_upazila(upazila: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    facilities = gpd.read_file(FACILITIES_PATH)
    facilities = facilities.set_crs("EPSG:4326") if facilities.crs is None else facilities
    upazila_wgs84 = upazila.to_crs("EPSG:4326")

    joined = gpd.sjoin(
        facilities,
        upazila_wgs84[["adm3_name", "adm3_pcode", "adm2_name", "geometry"]],
        how="left",
        predicate="within",
    )
    return joined.drop(columns=["index_right"])


if __name__ == "__main__":
    upazila_pop = load_upazila_population()
    n_matched = upazila_pop["total_pop"].notna().sum()
    print(f"upazila boundaries: {len(upazila_pop)}, matched to population: {n_matched}")
    upazila_pop.to_file(OUT_UPAZILA_PATH, driver="GeoJSON")

    facilities_joined = join_facilities_to_upazila(upazila_pop)
    n_facility_matched = facilities_joined["adm3_pcode"].notna().sum()
    print(f"facilities: {len(facilities_joined)}, matched to an upazila: {n_facility_matched}")
    facilities_joined.to_file(OUT_FACILITIES_PATH, driver="GeoJSON")

    print("wrote", OUT_UPAZILA_PATH, "and", OUT_FACILITIES_PATH)
