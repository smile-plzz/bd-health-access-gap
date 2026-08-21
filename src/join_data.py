"""Join upazila population to admin boundaries, and spatially join facilities
into their containing upazila. Writes the combined dataset to data/processed/.
"""

import re
from difflib import get_close_matches

import geopandas as gpd
import pandas as pd

BOUNDARIES_PATH = "data/raw/bgd_admin_boundaries/bgd_admin3.geojson"
POPULATION_PATH = "data/raw/bgd_admpop_adm3_2022.csv"
FACILITIES_PATH = "data/raw/osm_health_facilities.geojson"

OUT_UPAZILA_PATH = "data/processed/upazila_population.geojson"
OUT_FACILITIES_PATH = "data/processed/facilities_with_upazila.geojson"

# Administrative-unit suffixes that appear inconsistently between the two
# datasets (e.g. "Sadar Upazila" vs "Sadar") and would otherwise block an
# exact name match.
_ADMIN_SUFFIXES = (
    "upazila",
    "thana",
    "pourashava",
    "paurashava",
    "municipality",
    "city corporation",
    "cantonment",
)
FUZZY_CUTOFF = 0.82


def _normalize_name(name: str) -> str:
    """Lowercase, strip punctuation/admin suffixes, collapse whitespace.

    Meant to absorb the spelling/formatting variants between the census-era
    population CSV and the newer COD-AB boundary file (e.g. "Netrakona
    Sadar" vs "Netrokona Sadar Upazila").
    """
    if not isinstance(name, str):
        return ""
    s = name.lower().strip()
    s = re.sub(r"[.\-']", " ", s)
    for suffix in _ADMIN_SUFFIXES:
        s = re.sub(rf"\b{re.escape(suffix)}\b", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def match_population_to_boundaries(
    boundaries: pd.DataFrame,
    population: pd.DataFrame,
    dist_col_b: str = "adm2_name",
    sub_col_b: str = "adm3_name",
    dist_col_p: str = "ADM2_NAME",
    sub_col_p: str = "ADM3_NAME",
    fuzzy_cutoff: float = FUZZY_CUTOFF,
) -> tuple[list[int | None], list[str]]:
    """For each boundary row, find the best-matching population row index.

    Tries an exact match on normalized (district, upazila) name first, then
    falls back to a fuzzy match on the upazila name restricted to candidates
    in the same normalized district (never fuzzy-matches across districts).
    Returns (matched population row indices or None, match method per row)
    where method is one of "exact", "fuzzy", "ambiguous", "unmatched".
    """
    b_dist = boundaries[dist_col_b].map(_normalize_name)
    b_sub = boundaries[sub_col_b].map(_normalize_name)
    p_dist = population[dist_col_p].map(_normalize_name)
    p_sub = population[sub_col_p].map(_normalize_name)

    exact_index: dict[tuple[str, str], list[int]] = {}
    by_district: dict[str, dict[str, list[int]]] = {}
    for i, (d, s) in enumerate(zip(p_dist, p_sub)):
        exact_index.setdefault((d, s), []).append(i)
        by_district.setdefault(d, {}).setdefault(s, []).append(i)

    matches: list[int | None] = []
    methods: list[str] = []
    for d, s in zip(b_dist, b_sub):
        cands = exact_index.get((d, s))
        if cands:
            if len(cands) == 1:
                matches.append(cands[0])
                methods.append("exact")
            else:
                matches.append(cands[0])
                methods.append("ambiguous")
            continue

        pool = by_district.get(d, {})
        close = get_close_matches(s, pool.keys(), n=1, cutoff=fuzzy_cutoff)
        if close and len(pool[close[0]]) == 1:
            matches.append(pool[close[0]][0])
            methods.append("fuzzy")
        else:
            matches.append(None)
            methods.append("unmatched")
    return matches, methods


def load_upazila_population() -> gpd.GeoDataFrame:
    """Join population to boundaries by (district, upazila) name.

    The population CSV (older census pcode scheme, 544 units) and the
    boundary file (newer COD-AB v03 pcode scheme, 507 units) use
    incompatible ADM3_PCODE formats, so pcode join is not possible here.
    A plain lowercased exact name join only covers ~63% of upazilas
    (338/507); normalizing away admin-suffix/punctuation differences and
    falling back to a within-district fuzzy match on top of that closes
    most of the rest. Revisit with a proper pcode crosswalk before treating
    this as authoritative at national scale.
    """
    boundaries = gpd.read_file(BOUNDARIES_PATH)
    population = pd.read_csv(POPULATION_PATH, encoding="utf-8-sig")

    matches, methods = match_population_to_boundaries(boundaries, population)
    pop_cols = population[["F_TL", "M_TL", "T_TL"]].reindex(matches).reset_index(drop=True)

    merged = boundaries.reset_index(drop=True).copy()
    merged["female_pop"] = pop_cols["F_TL"].values
    merged["male_pop"] = pop_cols["M_TL"].values
    merged["total_pop"] = pop_cols["T_TL"].values
    merged["_pop_match_method"] = methods
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
    method_counts = upazila_pop["_pop_match_method"].value_counts().to_dict()
    print(f"upazila boundaries: {len(upazila_pop)}, matched to population: {n_matched} ({method_counts})")
    upazila_pop.drop(columns=["_pop_match_method"]).to_file(OUT_UPAZILA_PATH, driver="GeoJSON")

    facilities_joined = join_facilities_to_upazila(upazila_pop)
    n_facility_matched = facilities_joined["adm3_pcode"].notna().sum()
    print(f"facilities: {len(facilities_joined)}, matched to an upazila: {n_facility_matched}")
    facilities_joined.to_file(OUT_FACILITIES_PATH, driver="GeoJSON")

    print("wrote", OUT_UPAZILA_PATH, "and", OUT_FACILITIES_PATH)
