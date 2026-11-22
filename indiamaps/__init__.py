"""indiamaps: choropleth maps of Indian states and districts from a simple table."""

from . import colors
from .cards import CardFonts, CardText, chart_card, compact_map_card, map_card, save_card
from .charts import (
    SHORT_NAMES,
    colorbar,
    ranked_bar_chart,
    region_bar_chart,
    save_figure,
)
from .data import (
    STATE_ABBREVIATIONS,
    abbreviation,
    join_constituency_values,
    join_district_values,
    join_region,
    join_unit_values,
    join_values,
    load_boundaries,
    state_outlines,
)
from .maps import add_connector, add_labels, add_rupee_sign, plot_choropleth, plot_region_map, plot_state_map
from .regions import REGIONS, get_region
from .scales import build_custom_continuous_cmap, default_limits, make_norm

__version__ = "0.1.0"

__all__ = [
    "colors",
    "CardFonts",
    "CardText",
    "chart_card",
    "compact_map_card",
    "region_bar_chart",
    "join_constituency_values",
    "join_region",
    "join_unit_values",
    "plot_region_map",
    "REGIONS",
    "get_region",
    "map_card",
    "save_card",
    "SHORT_NAMES",
    "colorbar",
    "ranked_bar_chart",
    "save_figure",
    "STATE_ABBREVIATIONS",
    "abbreviation",
    "join_district_values",
    "join_values",
    "load_boundaries",
    "state_outlines",
    "add_connector",
    "add_labels",
    "add_rupee_sign",
    "plot_choropleth",
    "plot_state_map",
    "build_custom_continuous_cmap",
    "default_limits",
    "make_norm",
]
