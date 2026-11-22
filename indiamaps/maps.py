"""Drawing the map: coloured regions, grey for missing data, labels."""

from __future__ import annotations

import math

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from palettable.colorbrewer.sequential import Greys_9

from .data import state_outlines
from .regions import get_region
from .scales import make_norm

NO_DATA_COLOR = Greys_9.mpl_colors[1]

# Where the original notebooks drew the Chandigarh line: from open space on
# the left of Haryana to the city itself.
CHANDIGARH_LABEL_XY = (72.6, 29.4)
CHANDIGARH_TARGET_XY = (76.84, 30.74)


def get_font(font_path=None):
    """A matplotlib FontProperties for ``font_path``, or the default font (DejaVu Sans)."""
    if font_path:
        return fm.FontProperties(fname=str(font_path))
    return fm.FontProperties()


def plot_choropleth(
    merged,
    cmap,
    vmin,
    vmax,
    gamma=None,
    ax=None,
    figsize=(20, 20),
    column="value",
    no_data_color=NO_DATA_COLOR,
    edgecolor="0.1",
    linewidth=0.3,
    outline=None,
    outline_color="black",
    outline_width=0.5,
):
    """Draw the coloured map.

    Regions with a missing number are painted ``no_data_color`` (grey).
    ``gamma`` switches to a power scale: below 1 spreads out low values.
    ``outline`` is an optional GeoDataFrame, for example the state borders
    over a district map (see :func:`indiamaps.data.state_outlines`).
    Returns ``(fig, ax)``.
    """
    if ax is None:
        fig, ax = plt.subplots(1, figsize=figsize)
    else:
        fig = ax.figure
    merged.plot(ax=ax, color=no_data_color, linewidth=linewidth, edgecolor=edgecolor)
    have = merged[merged[column].notna()]
    if len(have):
        have.plot(
            ax=ax,
            column=column,
            cmap=cmap,
            alpha=1,
            linewidth=linewidth,
            edgecolor=edgecolor,
            norm=make_norm(vmin, vmax, gamma),
        )
    if outline is not None:
        outline.plot(ax=ax, facecolor="none", edgecolor=outline_color, linewidth=outline_width)
    ax.axis("off")
    return fig, ax


def format_value(value, mode="int", digits=0, prefix="", suffix=""):
    """Text for one number, the way the original notebooks wrote it.

    ``mode="int"`` rounds to a whole number, ``"float"`` keeps ``digits``
    decimals (and always shows at least one, so 3 becomes "3.0").
    """
    if mode == "float":
        return prefix + str(float(round(value, digits))) + suffix
    return prefix + str(int(round(value, 1))) + suffix


def add_labels(
    ax,
    merged,
    mode="int",
    digits=0,
    prefix="",
    suffix="",
    custom_col="custom",
    font_path=None,
    value_size=19,
    name_size=17,
    name_offset=0.6,
    label_offset=(0.0, 0.0),
    show_names=True,
    skip=(),
    color="black",
):
    """Write the number and the short name on each region.

    Modes:

    * ``"int"``: whole numbers.
    * ``"float"``: ``digits`` decimals.
    * ``"custom"``: text taken from the ``custom_col`` column of your table
      (join it in with ``custom_col=`` in :func:`indiamaps.data.join_values`).
    * ``"na"``: only the regions with no number, labelled "NA".

    ``prefix`` and ``suffix`` go around the number, for example ``suffix="%"``
    or ``prefix="₹"``. The default font has the rupee sign, but some fonts do
    not: then use :func:`add_rupee_sign` instead.
    ``skip`` is a list of region names to leave unlabelled.
    """
    if mode not in ("int", "float", "custom", "na"):
        raise ValueError("mode must be 'int', 'float', 'custom' or 'na'")
    prop = get_font(font_path)
    dx, dy = label_offset
    sizes = (value_size, name_size)
    if mode in ("custom", "na"):
        sizes = (value_size - 1, name_size - 1)
    for name, row in merged.iterrows():
        if name in skip or math.isnan(row["x"]):
            continue
        missing = math.isnan(row["value"])
        if mode == "na":
            if not missing:
                continue
            text = "NA"
        elif missing:
            continue
        elif mode == "custom":
            text = str(row[custom_col])
        else:
            text = format_value(row["value"], mode, digits, prefix, suffix)
        ax.text(row["x"] + dx, row["y"] + dy, text, fontsize=sizes[0], ha="center", fontproperties=prop, color=color)
        if show_names:
            ax.text(
                row["x"] + dx,
                row["y"] + dy + name_offset,
                row["short_name"],
                fontsize=sizes[1],
                ha="center",
                fontproperties=prop,
                color=color,
            )


def add_rupee_sign(ax, merged, offset=1.0, size=16, font_path=None, color="black"):
    """Put a rupee sign to the left of each number, for fonts that lack the glyph."""
    prop = get_font(font_path)
    for _, row in merged.iterrows():
        if math.isnan(row["value"]) or math.isnan(row["x"]):
            continue
        ax.text(row["x"] - offset, row["y"], "₹", fontsize=size, ha="center", fontproperties=prop, color=color)


def add_connector(
    ax,
    merged,
    region="Chandigarh",
    label_xy=CHANDIGARH_LABEL_XY,
    target_xy=CHANDIGARH_TARGET_XY,
    color="black",
):
    """Draw a thin line from a label placed in open space to a tiny region.

    Chandigarh is too small to hold its own label, so the label is moved to
    ``label_xy`` (pass the same point as ``label_points`` to
    :func:`indiamaps.data.join_values`) and a line joins it to the city. The
    line is only drawn when the region has a number.
    """
    if region not in merged.index or merged.loc[region, "value"] != merged.loc[region, "value"]:
        return
    ax.plot([label_xy[0], target_xy[0]], [label_xy[1], target_xy[1]], color)


def plot_state_map(
    merged,
    cmap,
    vmin,
    vmax,
    gamma=None,
    labels="int",
    digits=0,
    prefix="",
    suffix="",
    font_path=None,
    chandigarh_connector=False,
    figsize=(20, 20),
    **label_options,
):
    """One call for the usual state map: colours, labels and (optionally) the Chandigarh line.

    ``labels`` is one of ``"int"``, ``"float"``, ``"custom"``, ``"na"`` or
    ``None`` for no text. Returns ``(fig, ax)``.
    """
    fig, ax = plot_choropleth(merged, cmap, vmin, vmax, gamma=gamma, figsize=figsize)
    if chandigarh_connector:
        add_connector(ax, merged)
    if labels:
        add_labels(ax, merged, mode=labels, digits=digits, prefix=prefix, suffix=suffix, font_path=font_path, **label_options)
    return fig, ax


def plot_region_map(
    region,
    merged,
    cmap,
    vmin,
    vmax,
    boundaries=None,
    gamma="default",
    labels="default",
    digits=0,
    prefix="",
    suffix="",
    font_path=None,
    connector="default",
    outlines=(),
    figsize=(20, 20),
    **label_options,
):
    """Draw a map with the rules for one region (see :mod:`indiamaps.regions`).

    ``region`` is ``"states"``, ``"districts"``, ``"constituencies"``,
    ``"india_nepal_bhutan"`` or ``"subcontinent"``. Anything left as
    ``"default"`` takes the region's own setting: the scale (linear or power),
    whether numbers are printed on the map, the Chandigarh line, and state
    borders on top for districts and constituencies (these are made from
    ``boundaries``, the same file you joined).

    ``outlines`` adds more border layers: a list of GeoDataFrames, or of
    ``(GeoDataFrame, style)`` pairs where ``style`` is a dict of matplotlib
    line options such as ``{"linewidth": 1.0, "linestyle": ":"}``. The
    subcontinent map uses this for the country outline and disputed lines.
    Returns ``(fig, ax)``.
    """
    spec = get_region(region)
    if gamma == "default":
        gamma = spec.gamma
    if labels == "default":
        labels = "float" if (spec.labels and digits) else ("int" if spec.labels else None)
    if connector == "default":
        connector = spec.connector
    outline = None
    if spec.outline == "states" and boundaries is not None and spec.state_col in boundaries.columns:
        outline = state_outlines(boundaries, spec.state_col)
    fig, ax = plot_choropleth(merged, cmap, vmin, vmax, gamma=gamma, figsize=figsize, outline=outline)
    for layer in outlines:
        gdf, style = layer if isinstance(layer, tuple) else (layer, {})
        style = {"color": "black", "linewidth": 0.7, **style}
        gdf.plot(ax=ax, **style)
    if connector:
        add_connector(ax, merged)
    if labels:
        sizes = spec.label_sizes if spec.label_sizes[0] else (19, 17)
        label_options.setdefault("value_size", sizes[0])
        label_options.setdefault("name_size", sizes[1])
        add_labels(ax, merged, mode=labels, digits=digits, prefix=prefix, suffix=suffix, font_path=font_path, **label_options)
    return fig, ax
