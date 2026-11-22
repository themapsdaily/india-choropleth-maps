"""One test per region, each on tiny made-up square polygons."""

import math

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pytest
from shapely.geometry import box

import indiamaps as im
from indiamaps.regions import REGION_NAMES


def grid(names, extra=None):
    geoms = [box(i % 4 * 2, i // 4 * 2, i % 4 * 2 + 1.8, i // 4 * 2 + 1.8) for i in range(len(names))]
    data = {"st_nm": names}
    data.update(extra or {})
    return gpd.GeoDataFrame(data, geometry=geoms, crs="EPSG:4326")


CMAP = im.build_custom_continuous_cmap(im.colors.white, im.colors.scarlet_red)


def draw(region, merged, boundaries=None, **kw):
    fig, ax = im.plot_region_map(region, merged, CMAP, 0, 50, boundaries=boundaries, figsize=(5, 5), **kw)
    fig.canvas.draw()
    bars, _ = im.region_bar_chart(region, merged, im.colors.scarlet_red, figsize=(5, 5))
    plt.close(fig)
    plt.close(bars)
    return ax


def test_every_region_has_a_spec():
    assert set(REGION_NAMES) == set(im.REGIONS)
    with pytest.raises(ValueError):
        im.get_region("moon")


def test_states_with_custom_labels():
    b = grid(["Assam", "Goa", "Kerala", "Ladakh", "Jammu and Kashmir"])
    t = pd.DataFrame({"STATE": ["Assam", "Kerala"], "value": [10.0, 20.0], "label": ["Chile", None]})
    m = im.join_region("states", b, t, label_col="label")
    assert m.loc["Assam", "short_name"] == "Chile"
    assert m.loc["Kerala", "short_name"] == "KL"  # no custom text: falls back to the abbreviation
    assert math.isnan(m.loc["Goa", "value"])
    draw("states", m, b, prefix="$", suffix="B", digits=1)
    merged = im.join_region("states", b, t, ladakh="merged")
    assert "J&K and Ladakh" in merged.index


def test_states_table_xy_columns_move_labels():
    b = grid(["Assam", "Goa"])
    t = pd.DataFrame({"STATE": ["Assam"], "value": [1.0], "x": [50.0], "y": [60.0]})
    m = im.join_region("states", b, t)
    assert (m.loc["Assam", "x"], m.loc["Assam", "y"]) == (50.0, 60.0)


def test_districts_outline_and_gamma():
    b = grid(["d1", "d2", "d3", "d4"], {"dt_nm": ["A", "B", "A", "C"]})
    b["st_nm"] = ["Assam", "Assam", "Bihar", "Bihar"]
    t = pd.DataFrame({"DISTRICT": ["A", "A"], "STATE": ["Assam", "Bihar"], "value": [10.0, 30.0]})
    m = im.join_region("districts", b, t)
    assert m.loc["A, AS", "value"] == 10.0 and m.loc["A, BR", "value"] == 30.0
    ax = draw("districts", m, b)
    assert len(ax.collections) >= 3  # grey base, coloured, state outline


def test_constituencies_match_on_constituency_and_state():
    b = grid(["x"] * 4)
    b["pc_name"] = ["Pune", "Pune", "Patna", "Goa North"]
    b["st_nm"] = ["Maharashtra", "Karnataka", "Bihar", "Goa"]
    t = pd.DataFrame({"CONSTITUENCY": ["Pune"], "STATE": ["Maharashtra"], "value": [5.0]})
    m = im.join_region("constituencies", b, t)
    assert m.loc["Pune, MH", "value"] == 5.0
    assert math.isnan(m.loc["Pune, KA", "value"])
    draw("constituencies", m, b)


def test_india_nepal_bhutan_drops_bhutan_by_default():
    b = grid(["Assam", "Bihar", "Nepal", "Bhutan"])
    t = pd.DataFrame({"STATE": ["Assam", "Nepal", "Bhutan"], "value": [1.0, 2.0, 3.0]})
    m = im.join_region("india_nepal_bhutan", b, t)
    assert "Bhutan" not in m.index and "Nepal" in m.index
    assert im.abbreviation("Nepal") == "Nepal"
    kept = im.join_region("india_nepal_bhutan", b, t, exclude=())
    assert "Bhutan" in kept.index
    draw("india_nepal_bhutan", m, b)


def test_subcontinent_extra_outlines_and_short_names():
    b = grid(["Punjab(PK)", "Punjab", "Azad Kashmir", "Dhaka", "Province No. 1"])
    t = pd.DataFrame({"STATE": ["Punjab(PK)", "Punjab", "Azad Kashmir", "Dhaka", "Province No. 1"], "value": [5.0, 6, 7, 8, 9],
                      "x": [1, 3, 5, 7, 1], "y": [1, 1, 1, 1, 3]})
    m = im.join_region("subcontinent", b, t)
    assert m.loc["Punjab(PK)", "value"] == 5.0 and m.loc["Punjab", "value"] == 6.0  # told apart by exact name
    border = gpd.GeoDataFrame(geometry=[box(0, 0, 8, 4).boundary], crs="EPSG:4326")
    ax = draw("subcontinent", m, b, outlines=[(border, {"linewidth": 1.0, "linestyle": ":"}), border])
    fig, bax = im.region_bar_chart("subcontinent", m, im.colors.scarlet_red, figsize=(5, 5))
    labels = [t.get_text() for t in bax.get_yticklabels()]
    assert "PAK occupied J&K" in labels and "Koshi" in labels
    plt.close(fig)
