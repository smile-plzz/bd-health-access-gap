import pandas as pd

from join_data import _normalize_name, match_population_to_boundaries


def test_normalize_name_strips_admin_suffixes_and_punctuation():
    assert _normalize_name("Netrokona Sadar Upazila") == "netrokona sadar"
    assert _normalize_name("Kishoreganj Sadar") == "kishoreganj sadar"
    assert _normalize_name("Cox's Bazar Sadar") == "cox s bazar sadar"
    assert _normalize_name(None) == ""


def test_exact_match_after_normalization():
    boundaries = pd.DataFrame(
        {
            "adm2_name": ["Kishoreganj", "Kishoreganj"],
            "adm3_name": ["Sadar Upazila", "Tarail"],
        }
    )
    population = pd.DataFrame(
        {
            "ADM2_NAME": ["Kishoreganj", "Kishoreganj"],
            "ADM3_NAME": ["Sadar", "Tarail"],
        }
    )
    matches, methods = match_population_to_boundaries(boundaries, population)
    assert matches == [0, 1]
    assert methods == ["exact", "exact"]


def test_fuzzy_match_catches_spelling_variant_within_same_district():
    boundaries = pd.DataFrame(
        {
            "adm2_name": ["Kishoreganj"],
            "adm3_name": ["Kuliarchar"],
        }
    )
    population = pd.DataFrame(
        {
            "ADM2_NAME": ["Kishoreganj"],
            "ADM3_NAME": ["Kuliachar"],
        }
    )
    matches, methods = match_population_to_boundaries(boundaries, population)
    assert matches == [0]
    assert methods == ["fuzzy"]


def test_fuzzy_match_never_crosses_district_boundary():
    boundaries = pd.DataFrame(
        {
            "adm2_name": ["Kishoreganj"],
            "adm3_name": ["Kuliarchar"],
        }
    )
    population = pd.DataFrame(
        {
            "ADM2_NAME": ["Netrokona"],
            "ADM3_NAME": ["Kuliachar"],
        }
    )
    matches, methods = match_population_to_boundaries(boundaries, population)
    assert matches == [None]
    assert methods == ["unmatched"]


def test_unmatched_when_no_close_candidate():
    boundaries = pd.DataFrame(
        {
            "adm2_name": ["Kishoreganj"],
            "adm3_name": ["Austagram"],
        }
    )
    population = pd.DataFrame(
        {
            "ADM2_NAME": ["Kishoreganj"],
            "ADM3_NAME": ["Bajitpur"],
        }
    )
    matches, methods = match_population_to_boundaries(boundaries, population)
    assert matches == [None]
    assert methods == ["unmatched"]


def test_ambiguous_when_multiple_exact_candidates():
    boundaries = pd.DataFrame(
        {
            "adm2_name": ["Dhaka"],
            "adm3_name": ["Sadar"],
        }
    )
    population = pd.DataFrame(
        {
            "ADM2_NAME": ["Dhaka", "Dhaka"],
            "ADM3_NAME": ["Sadar", "Sadar"],
        }
    )
    matches, methods = match_population_to_boundaries(boundaries, population)
    assert matches == [0]
    assert methods == ["ambiguous"]
