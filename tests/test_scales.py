import numpy as np
import pytest

from indiamaps import build_custom_continuous_cmap, colors, make_norm
from indiamaps.colors import to_rgb255
from indiamaps.scales import default_limits


def test_two_colour_scale_ends_match_inputs():
    cmap = build_custom_continuous_cmap(colors.white, colors.dodger_blue)
    assert np.allclose(cmap(0.0)[:3], [1, 1, 1])
    assert np.allclose(cmap(1.0)[:3], np.array(colors.dodger_blue) / 255)


def test_three_colour_scale_passes_through_middle():
    cmap = build_custom_continuous_cmap(colors.royal_blue, colors.white, colors.scarlet_red)
    assert np.allclose(cmap(0.5)[:3], [1, 1, 1], atol=0.01)


def test_names_and_hex_are_accepted():
    assert to_rgb255("dodger_blue") == colors.dodger_blue
    assert to_rgb255("#ff0000") == [255, 0, 0]


def test_one_colour_is_an_error():
    with pytest.raises(ValueError):
        build_custom_continuous_cmap(colors.white)


def test_norms():
    assert make_norm(0, 10)(5) == 0.5
    assert make_norm(0, 10, gamma=0.5)(5) > 0.5
    assert default_limits([3, 9, float("nan")]) == (3.0, 9.0)
