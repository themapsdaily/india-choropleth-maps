"""What each map region expects and how it behaves.

Every region has a name, the columns it reads from the boundary file and from
your table, and the defaults the original notebooks used for it (labels,
borders drawn on top, power scale, how many bars to show).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

REGION_NAMES = ("states", "districts", "constituencies", "india_nepal_bhutan", "subcontinent")


@dataclass(frozen=True)
class RegionSpec:
    key: str
    title: str
    # Column in the boundary file with the region name (the unit name for
    # districts and constituencies).
    name_col: str
    # Column in the boundary file with the state, for regions that live inside states.
    state_col: Optional[str]
    # Matching columns in your table.
    table_name_col: str
    table_state_col: Optional[str]
    # Print numbers and short names on the map.
    labels: bool
    label_sizes: Tuple[int, int]
    # "none", or "states" (dissolve the units into state borders).
    outline: str = "none"
    gamma: Optional[float] = None
    # Chandigarh connector line is drawn by default.
    connector: bool = False
    # Bars shown by the ranked chart: ("all", n) or ("top", n).
    bars: Tuple[str, int] = ("all", 30)
    bar_font_size: int = 20
    bar_label_pad: int = 10
    bar_xlim: Tuple[float, float] = (0, 23)
    bar_figsize: Tuple[int, int] = (20, 21)
    card_layout: str = "state"
    # Boundary names to drop by default (for example a neighbouring country).
    exclude: Tuple[str, ...] = ()
    short_names: dict = field(default_factory=dict)
    description: str = ""


SUBCONTINENT_SHORT_NAMES = {
    "Punjab(PK)": " Punjab",
    "Azad Kashmir": "PAK occupied J&K",
    "Barisal": "Barishal",
    "Province No. 1": "Koshi",
}

REGIONS = {
    "states": RegionSpec(
        key="states",
        title="States and union territories",
        name_col="st_nm",
        state_col=None,
        table_name_col="STATE",
        table_state_col=None,
        labels=True,
        label_sizes=(19, 17),
        connector=True,
        bars=("all", 36),
        description="One shape per state or union territory. Ladakh can be separate or merged into Jammu and Kashmir.",
    ),
    "districts": RegionSpec(
        key="districts",
        title="Districts",
        name_col="dt_nm",
        state_col="st_nm",
        table_name_col="DISTRICT",
        table_state_col="STATE",
        labels=False,
        label_sizes=(0, 0),
        outline="states",
        gamma=0.3,
        bars=("top", 30),
        bar_label_pad=32,
        card_layout="district",
        description="One shape per district. State borders are drawn on top. Top and bottom 30 bar charts.",
    ),
    "constituencies": RegionSpec(
        key="constituencies",
        title="Parliamentary constituencies",
        name_col="pc_name",
        state_col="st_nm",
        table_name_col="CONSTITUENCY",
        table_state_col="STATE",
        labels=False,
        label_sizes=(0, 0),
        outline="states",
        bars=("top", 30),
        bar_label_pad=32,
        card_layout="district",
        description="One shape per Lok Sabha constituency, matched on constituency and state. State borders are drawn on top.",
    ),
    "india_nepal_bhutan": RegionSpec(
        key="india_nepal_bhutan",
        title="Indian states with Nepal and Bhutan",
        name_col="st_nm",
        state_col=None,
        table_name_col="STATE",
        table_state_col=None,
        labels=True,
        label_sizes=(19, 17),
        connector=True,
        bars=("all", 38),
        bar_font_size=22,
        bar_label_pad=32,
        bar_xlim=(-0.75, 23),
        bar_figsize=(20, 22),
        exclude=("Bhutan",),
        description="States plus the neighbouring countries as single shapes. Bhutan is left out by default; pass exclude=() to keep it.",
    ),
    "subcontinent": RegionSpec(
        key="subcontinent",
        title="South Asia",
        name_col="st_nm",
        state_col=None,
        table_name_col="STATE",
        table_state_col=None,
        labels=True,
        label_sizes=(15, 13),
        gamma=0.2,
        bars=("top", 30),
        bar_font_size=22,
        bar_label_pad=32,
        bar_xlim=(-0.75, 23),
        bar_figsize=(20, 22),
        card_layout="district",
        short_names=SUBCONTINENT_SHORT_NAMES,
        description="First-level divisions of every country in the region. Extra border layers (country outline, disputed lines) are passed as outlines.",
    ),
}


def get_region(region):
    """Return the spec for a region key, or raise a helpful error."""
    if isinstance(region, RegionSpec):
        return region
    try:
        return REGIONS[region]
    except KeyError:
        raise ValueError(f"Unknown region {region!r}. Choose one of {list(REGIONS)}") from None
