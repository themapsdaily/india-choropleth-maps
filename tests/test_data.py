import math

import pytest

from indiamaps import STATE_ABBREVIATIONS, abbreviation, join_district_values, join_values, state_outlines
from indiamaps.data import MERGED_LADAKH_NAME, label_point, state_key


def test_abbreviations_cover_36_unique_labels():
    assert len(STATE_ABBREVIATIONS) == 36
    assert len(set(STATE_ABBREVIATIONS.values())) == 36
    assert abbreviation("Odisha") == "OD"
    assert abbreviation("Somewhere Else") == "Somewhere Else"


def test_spellings_match():
    assert state_key("Keralam") == state_key("Kerala")
    assert state_key("NCT of Delhi") == state_key("Delhi")
    assert state_key("Orissa") == state_key("Odisha")
    assert state_key("Andaman & Nicobar Islands") == state_key("Andaman and Nicobar Islands")


def test_join_matches_missing_and_sorting(squares, table):
    merged = join_values(squares, table)
    assert merged.loc["Kerala", "value"] == 30.0  # matched through the Keralam alias
    assert math.isnan(merged.loc["Goa", "value"])  # no number: stays, will be grey
    assert list(merged.index[:3]) == ["Kerala", "Bihar", "Assam"]
    assert merged.index[-1] == "Goa"
    assert merged.loc["Assam", "short_name"] == "AS"


def test_label_points_are_inside_shapes(squares, table):
    merged = join_values(squares, table)
    for geom, x, y in zip(merged.geometry, merged["x"], merged["y"]):
        from shapely.geometry import Point

        assert geom.contains(Point(x, y))
    assert label_point(squares.geometry.iloc[0]).within(squares.geometry.iloc[0])


def test_label_point_override(squares, table):
    merged = join_values(squares, table, label_points={"Assam": (99, 98)})
    assert (merged.loc["Assam", "x"], merged.loc["Assam", "y"]) == (99, 98)


def test_ladakh_merge(squares, table):
    merged = join_values(squares, table, ladakh="merged")
    assert "Ladakh" not in merged.index
    assert MERGED_LADAKH_NAME in merged.index
    assert merged.loc[MERGED_LADAKH_NAME, "value"] == 5.0
    separate = join_values(squares, table, ladakh="separate")
    assert merged.loc[MERGED_LADAKH_NAME].geometry.area > separate.loc["Jammu and Kashmir"].geometry.area


def test_unmatched_rows_warn(squares, table):
    bad = table.copy()
    bad.loc[0, "STATE"] = "Atlantis"
    with pytest.warns(UserWarning):
        join_values(squares, bad)


def test_duplicate_rows_are_an_error(squares, table):
    with pytest.raises(ValueError):
        join_values(squares, table.iloc[[0, 0]])


def test_district_join_uses_district_and_state(squares):
    import pandas as pd

    districts = squares.rename(columns={"st_nm": "dt_nm"})
    districts["st_nm"] = ["Assam", "Assam", "Bihar", "Bihar", "Goa", "Goa"]
    districts["dt_nm"] = ["Same", "Other", "Same", "Third", "Same", "Fourth"]
    tbl = pd.DataFrame(
        {"DISTRICT": ["same", "Same"], "STATE": ["Assam", "Bihar"], "value": [1.0, 2.0]}
    )
    merged = join_district_values(districts, tbl)
    assert merged.loc["Same, AS", "value"] == 1.0
    assert merged.loc["Same, BR", "value"] == 2.0
    assert math.isnan(merged.loc["Same, GA", "value"])
    outlines = state_outlines(districts)
    assert len(outlines) == 3
