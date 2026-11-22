"""Browser front end for indiamaps.

Run with:  streamlit run app/streamlit_app.py

Upload a boundary file (a zip of a shapefile, or a GeoJSON) and a CSV with a
state column and a value column. Nothing is read from Google Drive or Sheets.
"""

from __future__ import annotations

import io
import os
import tempfile
import zipfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import indiamaps as im


def color_names():
    """Names of the colours in indiamaps.colors."""
    return list(im.colors.NAMED_COLORS)


def save_upload(data, filename, folder):
    """Write uploaded bytes to ``folder`` and return the path to hand to geopandas.

    A zip is unpacked and the path of the first .shp inside is returned.
    """
    safe = os.path.basename(filename)
    path = os.path.join(folder, safe)
    with open(path, "wb") as fh:
        fh.write(data)
    if safe.lower().endswith(".zip"):
        target = os.path.join(folder, "unzipped")
        os.makedirs(target, exist_ok=True)
        with zipfile.ZipFile(path) as zf:
            for member in zf.namelist():
                resolved = os.path.realpath(os.path.join(target, member))
                if not resolved.startswith(os.path.realpath(target) + os.sep) and resolved != os.path.realpath(target):
                    raise ValueError("The zip contains an unsafe path")
            zf.extractall(target)
        for root, _dirs, files in os.walk(target):
            for name in sorted(files):
                if name.lower().endswith((".shp", ".geojson", ".gpkg")):
                    return os.path.join(root, name)
        raise ValueError("No .shp, .geojson or .gpkg file found in the zip")
    return path


def read_boundaries(data, filename, name_col="st_nm"):
    with tempfile.TemporaryDirectory() as folder:
        return im.load_boundaries(save_upload(data, filename, folder), name_col=name_col)


def read_table(data):
    """Read an uploaded CSV. Lines starting with # are skipped."""
    return pd.read_csv(io.BytesIO(data), comment="#")


def save_font(data, filename, folder):
    """Save an uploaded font and return its path, or None when nothing was uploaded."""
    if not data:
        return None
    path = os.path.join(folder, os.path.basename(filename))
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def build_region_images(region, boundaries, table, color, vmin, vmax, gamma="default", digits=0, prefix="", suffix="",
                        ladakh="separate", font_path=None, text=None, label_col=None, **columns):
    """Make the map, colour bar, bar chart and cards for one region. Returns a dict of PIL images."""
    from PIL import Image

    spec = im.get_region(region)
    options = {"ladakh": ladakh, "label_col": label_col} if not spec.state_col else {}
    merged = im.join_region(region, boundaries, table, **options, **columns)
    cmap = im.build_custom_continuous_cmap(im.colors.white, color)
    out = {}
    with tempfile.TemporaryDirectory() as folder:
        fig, _ = im.plot_region_map(region, merged, cmap, vmin, vmax, boundaries=boundaries, gamma=gamma,
                                    digits=digits, prefix=prefix, suffix=suffix, font_path=font_path)
        im.save_figure(fig, f"{folder}/map.png", transparent=True)
        plt.close(fig)
        bar = im.colorbar(vmin, vmax, cmap, gamma=None if gamma == "default" else gamma)
        im.save_figure(bar, f"{folder}/colorbar.png")
        plt.close(bar)
        fig2, _ = im.region_bar_chart(region, merged, color, mode="float" if digits else "int", digits=digits,
                                      prefix=prefix, suffix=suffix, font_path=font_path)
        im.save_figure(fig2, f"{folder}/bars.png", transparent=True, tight=True)
        plt.close(fig2)
        fonts = im.CardFonts(heading=font_path, body=font_path, italic=font_path, italic_medium=font_path) if font_path else None
        text = text or im.CardText()
        out["map"] = im.map_card(f"{folder}/map.png", f"{folder}/colorbar.png", text, fonts=fonts, layout=spec.card_layout)
        out["bars"] = im.chart_card(f"{folder}/bars.png", text, fonts=fonts, layout=spec.card_layout)
    return out


def main():
    import streamlit as st

    st.set_page_config(page_title="indiamaps", initial_sidebar_state="collapsed")
    st.title("Maps from a table")
    region = st.selectbox("Region", list(im.REGIONS), format_func=lambda k: im.REGIONS[k].title)
    spec = im.get_region(region)
    st.caption(spec.description)
    names = color_names()
    color = im.colors.NAMED_COLORS[st.selectbox("Colour", names, index=names.index("dodger_blue"))]
    font_file = st.file_uploader("Optional font file (otf or ttf). Leave empty for DejaVu Sans.", type=["otf", "ttf"])
    folder = tempfile.mkdtemp()
    font_path = save_font(font_file.getvalue(), font_file.name, folder) if font_file else None
    prefix = st.text_input("Prefix", "")
    suffix = st.text_input("Suffix", "")

    boundary = st.file_uploader("Boundary file: zip of a shapefile, or GeoJSON", type=["zip", "geojson", "json", "gpkg"])
    csv = st.file_uploader("CSV with your numbers", type=["csv"])
    if not (boundary and csv):
        wanted = [spec.table_name_col] + ([spec.table_state_col] if spec.table_state_col else []) + ["value"]
        st.info("Upload both files. The CSV needs the columns: " + ", ".join(wanted) + ".")
        return
    name_col = st.text_input("Name column in the boundary file", spec.name_col)
    columns = {"name_col": name_col, "table_name_col": st.text_input("Name column in the CSV", spec.table_name_col)}
    if spec.state_col:
        columns["state_col"] = st.text_input("State column in the boundary file", spec.state_col)
        columns["table_state_col"] = st.text_input("State column in the CSV", spec.table_state_col)
    try:
        boundaries = read_boundaries(boundary.getvalue(), boundary.name, name_col)
        table = read_table(csv.getvalue())
    except Exception as exc:
        st.error(f"Could not read the files: {exc}")
        return
    vmin = st.number_input("Scale minimum", value=float(table["value"].min()))
    vmax = st.number_input("Scale maximum", value=float(table["value"].max()))
    power = st.selectbox("Scale", ["Region default", "Linear", "Power"])
    gamma = {"Region default": "default", "Linear": None}.get(power)
    if power == "Power":
        gamma = st.number_input("Power (gamma)", value=0.5, min_value=0.05)
    digits = int(st.number_input("Decimal places", value=0, step=1, min_value=0))
    ladakh = st.selectbox("Ladakh", ["separate", "merged"]) if region == "states" else "separate"
    text = im.CardText(
        header_1=st.text_input("Header 1", ""),
        header_2=st.text_input("Header 2", ""),
        sub_header_1=st.text_input("Sub header 1", ""),
        sub_header_2=st.text_input("Sub header 2", ""),
        scale_min=f"{prefix}{vmin:g}{suffix}",
        scale_max=f"{prefix}{vmax:g}{suffix}",
        copyright=st.text_input("Credit line", ""),
        footer_1=st.text_input("Footer 1", "Scale:"),
        footer_2=st.text_input("Footer 2", "Source:"),
        footer_4="Areas in grey, if any, have no data.",
    )
    try:
        images = build_region_images(region, boundaries, table, color, vmin, vmax, gamma, digits, prefix, suffix,
                                     ladakh, font_path, text, **columns)
    except Exception as exc:
        st.error(f"Could not draw the map: {exc}")
        return
    for key in ("map", "bars"):
        st.image(images[key])
        buf = io.BytesIO()
        images[key].save(buf, format="PNG")
        st.download_button(f"Download {key} card", buf.getvalue(), f"{key}.png", "image/png")


if __name__ == "__main__":
    main()
