"""Colour scales and normalisation."""

from __future__ import annotations

import matplotlib.colors as mcolors
import numpy as np

from .colors import to_rgb255


def inter_from_256(x):
    """Map a value from the 0 to 255 range onto 0 to 1."""
    return np.interp(x=x, xp=[0, 255], fp=[0, 1])


def build_custom_continuous_cmap(*rgb_list):
    """Build a smooth colour map that runs through the colours you give it.

    Pass two colours for a simple light-to-dark scale, or three or more to
    pass through the middle ones, for example blue, white, red for numbers
    that go both below and above zero. Each colour can be an ``[R, G, B]``
    list (0 to 255), a name from :mod:`indiamaps.colors`, or a hex string.
    """
    if len(rgb_list) < 2:
        raise ValueError("Give at least two colours")
    rgb_list = [to_rgb255(c) for c in rgb_list]
    n_section = len(rgb_list) - 1
    cdict = {}
    for channel, key in enumerate(("red", "green", "blue")):
        cdict[key] = tuple(
            (i / n_section, inter_from_256(rgb[channel]), inter_from_256(rgb[channel]))
            for i, rgb in enumerate(rgb_list)
        )
    return mcolors.LinearSegmentedColormap("new_cmap", segmentdata=cdict)


def make_norm(vmin, vmax, gamma=None):
    """Return the normaliser for a scale.

    ``gamma=None`` gives an even (linear) scale. A ``gamma`` below 1 spreads
    out the low values, above 1 spreads out the high values.
    """
    if gamma is None:
        return mcolors.Normalize(vmin=vmin, vmax=vmax)
    return mcolors.PowerNorm(gamma=gamma, vmin=vmin, vmax=vmax)


def default_limits(values, vmin=None, vmax=None):
    """Fill in a missing ``vmin`` or ``vmax`` from the data."""
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if vmin is None:
        vmin = float(values.min()) if values.size else 0.0
    if vmax is None:
        vmax = float(values.max()) if values.size else 1.0
    return vmin, vmax
