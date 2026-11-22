import importlib.util
import io
import pathlib
import zipfile

import pytest

APP = pathlib.Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


@pytest.fixture(scope="module")
def app():
    spec = importlib.util.spec_from_file_location("streamlit_app", APP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_color_names(app):
    assert "dodger_blue" in app.color_names()


def test_read_table_skips_comment_lines(app):
    df = app.read_table(b"# made up\nSTATE,value\nGoa,1\n")
    assert list(df.columns) == ["STATE", "value"]


def test_boundaries_from_geojson_and_zip(app, squares):
    data = squares.to_json().encode()
    assert len(app.read_boundaries(data, "b.geojson")) == 6
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("inner/b.geojson", data)
    assert len(app.read_boundaries(buf.getvalue(), "b.zip")) == 6


def test_unsafe_zip_is_refused(app, tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../evil.txt", "x")
    with pytest.raises(ValueError):
        app.save_upload(buf.getvalue(), "z.zip", str(tmp_path))


def test_build_region_images(app, squares, table):
    out = app.build_region_images("states", squares, table, [26, 167, 238], 0, 40)
    assert out["map"].size == (4000, 4000)
