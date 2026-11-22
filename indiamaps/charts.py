"""Colour bar and ranked bar chart."""

from __future__ import annotations

import matplotlib.font_manager as fm
import matplotlib.patches as patches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyBboxPatch

from .colors import to_unit
from .maps import format_value, get_font
from .scales import make_norm

SHORT_NAMES = {
    "Dadra and Nagar Haveli and Daman and Diu": "DNHDD",
    "Andaman and Nicobar Islands": "Andaman & Nicobar",
    "Jammu and Kashmir": "Jammu & Kashmir",
    "Kerala": "Keralam",
}


# ---------------------------------------------------------------- colour bar

def colorbar(vmin, vmax, cmap, gamma=None, figsize=(20, 20), orientation="horizontal"):
    """A colour bar with rounded ends and no tick labels.

    The min and max numbers are added later, usually by the social card, so
    they can use the card's font. Returns the figure; save it with
    :func:`save_figure`. The geometry (a 20 by 20 inch figure) matches what
    :mod:`indiamaps.cards` expects by default.
    """
    fig, ax = plt.subplots(1, figsize=figsize)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=make_norm(vmin, vmax, gamma))
    cb = fig.colorbar(sm, ax=ax, orientation=orientation)
    cb.set_ticks([])
    Path = mpath.Path
    cb.outline.set_visible(False)
    bot, top = -0.05, 1.05

    def flip(xy):
        return xy[:, ::-1] if orientation == "horizontal" else xy

    curve = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    end_cap = flip(np.array([[0, 1], [0, top], [1, top], [1, 1]]))
    start_cap = flip(np.array([[0, 0], [0, bot], [1, bot], [1, 0]]))
    for xy, color in ((end_cap, cmap(1.0)), (start_cap, cmap(0.0))):
        cb.ax.add_patch(
            patches.PathPatch(
                mpath.Path(xy, curve),
                facecolor=color,
                linewidth=0,
                antialiased=False,
                transform=cb.ax.transAxes,
                clip_on=False,
            )
        )
    outline = flip(np.array([[0, 0], [0, bot], [1, bot], [1, 0], [1, 1], [1, top], [0, top], [0, 1], [0, 0]]))
    outline_codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO]
    cb.ax.add_patch(
        patches.PathPatch(
            mpath.Path(outline, outline_codes, closed=True),
            facecolor="None",
            lw=1,
            transform=cb.ax.transAxes,
            clip_on=False,
        )
    )
    return fig


def save_figure(fig, path, dpi=300, transparent=False, tight=False):
    """Save a figure, making the folder first if needed."""
    import os

    folder = os.path.dirname(os.fspath(path))
    if folder:
        os.makedirs(folder, exist_ok=True)
    kwargs = {"bbox_inches": "tight"} if tight else {}
    fig.savefig(path, dpi=dpi, transparent=transparent, **kwargs)


# ------------------------------------------------------------ ranked bars

def ranked_bar_chart(
    merged,
    color,
    which="all",
    n=30,
    ax=None,
    figsize=(20, 21),
    xlim=(0, 23),
    font_path=None,
    mode="int",
    digits=0,
    prefix="",
    suffix="",
    short_names=SHORT_NAMES,
    label_pad=10,
    font_size=20,
    max_bar=22,
    min_bar=0.2,
    rounding_size=0.12,
    flag_col=None,
    flag_zoom=0.075,
):
    """Horizontal bars, longest at the top, with rounded ends and value labels.

    ``which`` picks the rows to show, always ranked from high to low:

    * ``"all"``: every region that has a number.
    * ``"top"``: the highest ``n``.
    * ``"bottom"``: the lowest ``n``.
    * ``"middle"``: everything below the top ``n``.

    ``color`` is the bar colour (``[R, G, B]`` 0 to 255, a colour name or hex).
    Bar lengths are scaled so the biggest value in ``merged`` reaches
    ``max_bar`` (the axis runs ``xlim``), with ``min_bar`` added so a value
    near zero still shows. ``short_names`` maps long names to the short form
    shown on the axis. ``flag_col`` is an optional column of image paths drawn
    to the left of the names. Returns ``(fig, ax)``.
    """
    if which not in ("all", "top", "bottom", "middle"):
        raise ValueError("which must be 'all', 'top', 'bottom' or 'middle'")
    data = merged[merged["value"].notna()].sort_values("value", ascending=False)
    biggest = data["value"].max()
    if which == "top":
        data = data.iloc[:n]
    elif which == "bottom":
        data = data.iloc[-n:]
    elif which == "middle":
        data = data.iloc[n:]
    data = data.copy()
    data["bar"] = data["value"] / biggest * max_bar + min_bar
    names = [(short_names or {}).get(i, i) for i in data.index]

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure
    prop = get_font(font_path)
    rgb = to_unit(color)
    ax.barh(range(len(data)), data["bar"], color=rgb, align="center")
    for side in ("top", "bottom", "left", "right"):
        ax.spines[side].set_visible(False)
    ax.xaxis.set_ticks_position("none")
    ax.yaxis.set_ticks_position("none")
    ax.xaxis.set_tick_params(pad=5)
    ax.yaxis.set_tick_params(pad=label_pad)
    ax.xaxis.set_visible(False)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels(names, fontproperties=prop, fontsize=font_size)
    ax.invert_yaxis()
    ax.set(xlim=list(xlim))

    new_patches = []
    for patch in list(ax.patches):
        bb = patch.get_bbox()
        fc = patch.get_facecolor()
        new_patches.append(
            FancyBboxPatch(
                (bb.xmin, bb.ymin),
                abs(bb.width),
                abs(bb.height),
                boxstyle=f"round,pad=-0.0040,rounding_size={rounding_size}",
                ec="none",
                fc=fc,
                mutation_aspect=4,
            )
        )
        patch.remove()
    for p in new_patches:
        ax.add_patch(p)

    for i, (width, value) in enumerate(zip(data["bar"], data["value"])):
        ax.text(
            width + 0.1,
            i,
            format_value(value, mode, digits, prefix, suffix),
            fontsize=font_size,
            color="black",
            fontweight="bold",
            fontproperties=prop,
            va="center",
        )

    if flag_col is not None:
        for i, path in enumerate(data[flag_col]):
            image = OffsetImage(plt.imread(path), zoom=flag_zoom)
            ax.add_artist(AnnotationBbox(image, (-0.75, i), frameon=False))
    return fig, ax


def region_bar_chart(region, merged, color, which=None, n=None, **options):
    """:func:`ranked_bar_chart` with the region's own defaults (rows shown, figure size, label gap, font size, axis range, short names)."""
    from .regions import get_region

    spec = get_region(region)
    default_which, default_n = spec.bars
    options.setdefault("figsize", spec.bar_figsize)
    options.setdefault("xlim", spec.bar_xlim)
    options.setdefault("label_pad", spec.bar_label_pad)
    options.setdefault("font_size", spec.bar_font_size)
    if "short_names" not in options:
        options["short_names"] = {**SHORT_NAMES, **spec.short_names}
    return ranked_bar_chart(merged, color, which=which or default_which, n=n or default_n, **options)
