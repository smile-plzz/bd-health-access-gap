"""Geocode facility addresses/names to lat/lon coordinates."""

import time

import pandas as pd
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode_place(name: str, country: str = "Bangladesh") -> tuple[float, float] | None:
    """Look up a place name via Nominatim, return (lat, lon) or None."""
    params = {"q": f"{name}, {country}", "format": "json", "limit": 1}
    headers = {"User-Agent": "bd-health-access-gap-research"}
    resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    results = resp.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])


def geocode_dataframe(df: pd.DataFrame, name_col: str, delay: float = 1.0) -> pd.DataFrame:
    """Geocode every row's name_col, add lat/lon columns. Respects Nominatim's 1 req/sec limit."""
    lats, lons = [], []
    for name in df[name_col]:
        coords = geocode_place(name)
        lats.append(coords[0] if coords else None)
        lons.append(coords[1] if coords else None)
        time.sleep(delay)
    df = df.copy()
    df["lat"] = lats
    df["lon"] = lons
    return df
