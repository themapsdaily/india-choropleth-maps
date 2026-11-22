import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

NAMES = ["Assam", "Bihar", "Goa", "Kerala", "Jammu and Kashmir", "Ladakh"]


@pytest.fixture
def squares():
    """Six tiny square 'states' on a grid. Not real boundaries."""
    geoms = [box(i % 3 * 2, i // 3 * 2, i % 3 * 2 + 1.8, i // 3 * 2 + 1.8) for i in range(len(NAMES))]
    return gpd.GeoDataFrame({"st_nm": NAMES}, geometry=geoms, crs="EPSG:4326")


@pytest.fixture
def table():
    return pd.DataFrame(
        {
            "STATE": ["Assam", "Bihar", "Keralam", "Jammu and Kashmir", "Ladakh"],
            "value": [10.0, 20.0, 30.0, 5.0, 8.0],
        }
    )
