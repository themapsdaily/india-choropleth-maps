"""Named colours used in the original notebooks.

Every colour is an ``[R, G, B]`` list with values from 0 to 255. Use them by
name, for example ``indiamaps.colors.dodger_blue``, or pass the name as a
string to :func:`indiamaps.scales.build_custom_continuous_cmap`.
"""

from __future__ import annotations

white = [255, 255, 255]
persian_green = [2, 181, 155]
light_green = [144, 238, 144]
citrus_green = [106, 181, 0]
olive_green = [91, 155, 15]
bottle_green = [1, 56, 0]
yellow = [255, 157, 1]
light_yellow = [255, 255, 167]
golden_yellow = [255, 197, 2]
dark_orange = [255, 136, 0]
radical_red = [255, 56, 84]
scarlet_red = [255, 50, 23]
pink = [255, 98, 131]
purple = [150, 84, 229]
medium_purple = [164, 94, 233]
royal_blue = [52, 138, 234]
cornflower_blue = [88, 178, 240]
sky_blue = [123, 217, 246]
dodger_blue = [26, 167, 238]
turquoise_blue = [41, 218, 228]
pacific_blue = [0, 149, 255]
navy_blue = [2, 5, 90]
yale_blue = [0, 76, 151]
grey = [155, 155, 155]

NAMED_COLORS = {
    name: value
    for name, value in dict(globals()).items()
    if isinstance(value, list) and len(value) == 3 and not name.startswith("_")
}


def to_rgb255(color):
    """Turn a colour into an ``[R, G, B]`` list with values from 0 to 255.

    Accepts a name from this module, a hex string such as ``"#1AA7EE"``, an
    ``[R, G, B]`` list or tuple with values from 0 to 255, or a matplotlib
    colour name such as ``"tab:red"``.
    """
    if isinstance(color, str):
        if color in NAMED_COLORS:
            return list(NAMED_COLORS[color])
        from matplotlib.colors import to_rgb

        return [round(v * 255) for v in to_rgb(color)]
    values = list(color)
    if len(values) < 3:
        raise ValueError(f"A colour needs three numbers, got {color!r}")
    return [float(v) for v in values[:3]]


def to_unit(color):
    """Same as :func:`to_rgb255` but scaled to 0 to 1, as matplotlib expects."""
    return [v / 255 for v in to_rgb255(color)]
