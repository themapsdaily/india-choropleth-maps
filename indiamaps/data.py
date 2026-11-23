"""Loading boundary files and joining your numbers onto them."""

from __future__ import annotations

import re
import warnings

import geopandas as gpd
import pandas as pd

from .regions import get_region

# Short labels printed on the map.
STATE_ABBREVIATIONS = {
    "Andaman and Nicobar Islands": "A&N",
    "Andhra Pradesh": "AP",
    "Arunachal Pradesh": "AR",
    "Assam": "AS",
    "Bihar": "BR",
    "Chandigarh": "CH",
    "Chhattisgarh": "CG",
    "Dadra and Nagar Haveli and Daman and Diu": "DNHDD",
    "Delhi": "DL",
    "Goa": "GA",
    "Gujarat": "GJ",
    "Haryana": "HR",
    "Himachal Pradesh": "HP",
    "Jammu and Kashmir": "J&K",
    "Jharkhand": "JH",
    "Karnataka": "KA",
    "Kerala": "KL",
    "Ladakh": "LA",
    "Lakshadweep": "LD",
    "Madhya Pradesh": "MP",
    "Maharashtra": "MH",
    "Manipur": "MN",
    "Meghalaya": "ML",
    "Mizoram": "MZ",
    "Nagaland": "NL",
    "Odisha": "OD",
    "Puducherry": "PY",
    "Punjab": "PB",
    "Rajasthan": "RJ",
    "Sikkim": "SK",
    "Tamil Nadu": "TN",
    "Telangana": "TS",
    "Tripura": "TR",
    "Uttar Pradesh": "UP",
    "Uttarakhand": "UK",
    "West Bengal": "WB",
}

# Other spellings that point to the same place. Keys and values are written
# the way normalise_name() writes them.
STATE_ALIASES = {
    "keralam": "kerala",
    "orissa": "odisha",
    "uttaranchal": "uttarakhand",
    "pondicherry": "puducherry",
    "chattisgarh": "chhattisgarh",
    "nct of delhi": "delhi",
    "national capital territory of delhi": "delhi",
    "andaman and nicobar": "andaman and nicobar islands",
    "andaman nicobar islands": "andaman and nicobar islands",
    "dnhdd": "dadra and nagar haveli and daman and diu",
    "dadra nagar haveli and daman diu": "dadra and nagar haveli and daman and diu",
    "dadra and nagar haveli and daman and diu": "dadra and nagar haveli and daman and diu",
    "jammu kashmir": "jammu and kashmir",
    "j and k": "jammu and kashmir",
}

MERGED_LADAKH_NAME = "J&K and Ladakh"


def normalise_name(name):
    """Lower-case a name and strip punctuation so spellings can be compared."""
    text = str(name).strip().lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return text


def state_key(name):
    """The comparison key for a state or union territory name."""
    key = normalise_name(name)
    return STATE_ALIASES.get(key, key)


_ABBREVIATION_BY_KEY = {state_key(k): v for k, v in STATE_ABBREVIATIONS.items()}


def abbreviation(name):
    """Short label for a state, or the full name if we do not know it."""
    return _ABBREVIATION_BY_KEY.get(state_key(name), str(name))


def load_boundaries(path, name_col="st_nm", crs="EPSG:4326"):
    """Read a boundary file (GeoJSON, GeoPackage, shapefile) with geopandas.

    The file must have a column with the region names. The result is
    reprojected to longitude and latitude so that label positions are in
    degrees. We do not ship any boundary file: use your own.
    """
    gdf = gpd.read_file(path)
    if name_col is not None and name_col not in gdf.columns:
        raise KeyError(
            f"Column {name_col!r} not found in {path}. Columns are: {list(gdf.columns)}. "
            "Pass name_col= with the right column."
        )
    if crs is not None and gdf.crs is not None and str(gdf.crs) != str(crs):
        gdf = gdf.to_crs(crs)
    return gdf


def label_point(geometry):
    """A point guaranteed to be inside the shape, for placing a label.

    For shapes made of several parts (islands, for example) the point is
    taken from the biggest part.
    """
    if geometry is None or geometry.is_empty:
        return None
    if geometry.geom_type == "MultiPolygon":
        geometry = max(geometry.geoms, key=lambda g: g.area)
    return geometry.representative_point()


def _add_label_points(frame, label_points=None):
    xs, ys = [], []
    for name, geom in zip(frame.index, frame.geometry):
        if label_points and name in label_points:
            x, y = label_points[name]
        else:
            point = label_point(geom)
            x, y = (point.x, point.y) if point is not None else (float("nan"), float("nan"))
        xs.append(x)
        ys.append(y)
    frame["x"] = xs
    frame["y"] = ys
    return frame


def _prepare_table(table, name_col, value_col, custom_col, extra_cols=()):
    keep = [name_col, value_col] + ([custom_col] if custom_col else []) + [c for c in extra_cols if c not in (name_col, value_col, custom_col)]
    missing = [c for c in keep if c not in table.columns]
    if missing:
        raise KeyError(f"Columns {missing} not found in your table. Columns are: {list(table.columns)}")
    out = table[keep].copy()
    out[value_col] = pd.to_numeric(out[value_col], errors="coerce")
    rename = {name_col: "_name", value_col: "value"}
    if custom_col:
        rename[custom_col] = "custom"
    return out.rename(columns=rename)


def merge_ladakh(boundaries, name_col="st_nm"):
    """Fold Ladakh into Jammu and Kashmir and call the result "J&K and Ladakh"."""
    keys = boundaries[name_col].map(state_key)
    is_jk = keys == "jammu and kashmir"
    is_ladakh = keys == "ladakh"
    if not is_ladakh.any():
        return boundaries.copy()
    parts = boundaries[is_jk | is_ladakh]
    union = parts.geometry.union_all()
    out = boundaries[~is_ladakh].copy()
    jk_index = out.index[out[name_col].map(state_key) == "jammu and kashmir"]
    if len(jk_index) == 0:
        raise ValueError("Cannot merge Ladakh: no Jammu and Kashmir row in the boundary file")
    out.loc[jk_index[0], "geometry"] = union
    out.loc[jk_index[0], name_col] = MERGED_LADAKH_NAME
    return out


def join_values(
    boundaries,
    table,
    name_col="st_nm",
    table_name_col="STATE",
    value_col="value",
    custom_col=None,
    ladakh="separate",
    label_points=None,
    warn_unmatched=True,
    exclude=(),
    label_col=None,
    extra_cols=(),
):
    """Attach your numbers to a boundary file with one row per state (or country, or province).

    Parameters
    ----------
    boundaries : GeoDataFrame from :func:`load_boundaries`.
    table : DataFrame with one row per state and a number.
    name_col : state name column in the boundary file.
    table_name_col : state name column in your table.
    value_col : column in your table holding the number to map.
    custom_col : optional column with ready-made label text, for the
        ``"custom"`` label mode.
    ladakh : ``"separate"`` keeps Ladakh as its own region. ``"merged"``
        folds it into Jammu and Kashmir and uses that state's number.
    label_points : optional ``{name: (x, y)}`` to move a label by hand. If
        your table has ``x`` and ``y`` columns they are used the same way.
    exclude : names in the boundary file to drop (for example ``["Bhutan"]``).
    label_col : optional column in your table with the short text printed
        under each number, instead of the built-in abbreviation (the custom
        styling notebook uses this).
    extra_cols : other table columns to carry through, for example an image
        path column for flags.

    Returns a GeoDataFrame indexed by region name with the columns
    ``value``, ``short_name``, ``x``, ``y`` (the label position),
    ``geometry`` and, if asked, ``custom``. Sorted from high to low, with
    missing values last. States with no number stay in the frame with a
    missing value, so they are drawn grey.
    """
    if ladakh not in ("separate", "merged"):
        raise ValueError("ladakh must be 'separate' or 'merged'")
    base = merge_ladakh(boundaries, name_col) if ladakh == "merged" else boundaries.copy()
    if exclude:
        drop = {state_key(n) for n in exclude}
        base = base[~base[name_col].map(state_key).isin(drop)]
    base = base[[name_col, "geometry"]].copy()
    base["_key"] = base[name_col].map(state_key)
    # The merged J&K + Ladakh shape takes Jammu and Kashmir's number.
    base.loc[base[name_col] == MERGED_LADAKH_NAME, "_key"] = state_key("Jammu and Kashmir")

    wanted = list(extra_cols) + ([label_col] if label_col else [])
    wanted += [c for c in ("x", "y") if c in table.columns and c not in wanted]
    tbl = _prepare_table(table, table_name_col, value_col, custom_col, wanted)
    tbl["_key"] = tbl["_name"].map(state_key)
    if tbl["_key"].duplicated().any():
        dupes = tbl.loc[tbl["_key"].duplicated(keep=False), "_name"].tolist()
        raise ValueError(f"Your table lists these regions more than once: {dupes}")

    if warn_unmatched:
        unmatched = sorted(set(tbl["_key"]) - set(base["_key"]))
        if ladakh == "merged" and "ladakh" in unmatched:
            unmatched.remove("ladakh")
        if unmatched:
            names = tbl.loc[tbl["_key"].isin(unmatched), "_name"].tolist()
            warnings.warn(f"Rows in your table that match no region in the boundary file: {names}")

    cols = ["_key", "value"] + (["custom"] if custom_col else []) + [c for c in tbl.columns if c in wanted]
    merged = base.merge(tbl[cols], on="_key", how="left", suffixes=("", "_tbl"))
    # Keep the boundary's own spelling for the full name.
    merged["short_name"] = [
        MERGED_LADAKH_NAME if n == MERGED_LADAKH_NAME else abbreviation(n) for n in merged[name_col]
    ]
    if label_col:
        given = merged[label_col].astype("object")
        merged["short_name"] = given.where(given.notna(), merged["short_name"]).astype(str)
        merged = merged.drop(columns=label_col)
    merged = merged.drop(columns="_key").set_index(name_col)
    merged.index.name = None
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=boundaries.crs)
    typed_points = {}
    if "x" in merged.columns and "y" in merged.columns:
        for name, x, y in zip(merged.index, merged["x"], merged["y"]):
            if pd.notna(x) and pd.notna(y):
                typed_points[name] = (x, y)
        merged = merged.drop(columns=["x", "y"])
    merged = _add_label_points(merged, {**typed_points, **(label_points or {})})
    merged = merged.sort_values(by="value", ascending=False, na_position="last")
    return merged


def join_unit_values(
    boundaries,
    table,
    unit_col,
    state_col="st_nm",
    table_unit_col="DISTRICT",
    table_state_col="STATE",
    value_col="value",
):
    """Attach your numbers to a boundary file of units inside states (districts, constituencies).

    Names repeat across states, so rows are matched on unit and state
    together. The result is indexed by ``"Unit, ST"`` (the state
    abbreviation) and sorted from high to low.
    """
    for col in (unit_col, state_col):
        if col not in boundaries.columns:
            raise KeyError(f"Column {col!r} not found in the boundary file. Columns are: {list(boundaries.columns)}")
    base = boundaries[[unit_col, state_col, "geometry"]].copy()
    base["_key"] = base[unit_col].map(normalise_name) + "|" + base[state_col].map(state_key)

    keep = [table_unit_col, table_state_col, value_col]
    missing = [c for c in keep if c not in table.columns]
    if missing:
        raise KeyError(f"Columns {missing} not found in your table. Columns are: {list(table.columns)}")
    tbl = table[keep].copy()
    tbl["value"] = pd.to_numeric(tbl[value_col], errors="coerce")
    tbl["_key"] = tbl[table_unit_col].map(normalise_name) + "|" + tbl[table_state_col].map(state_key)
    if tbl["_key"].duplicated().any():
        raise ValueError("Your table lists some rows more than once")
    unmatched = sorted(set(tbl["_key"]) - set(base["_key"]))
    if unmatched:
        warnings.warn(f"{len(unmatched)} rows in your table match nothing in the boundary file, for example {unmatched[:3]}")

    merged = base.merge(tbl[["_key", "value"]], on="_key", how="left")
    merged["short_name"] = merged[state_col].map(abbreviation)
    merged["name"] = merged[unit_col] + ", " + merged["short_name"]
    merged = merged.drop(columns="_key").set_index("name")
    merged.index.name = None
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=boundaries.crs)
    return merged.sort_values(by="value", ascending=False, na_position="last")


def join_district_values(boundaries, table, district_col="dt_nm", state_col="st_nm",
                         table_district_col="DISTRICT", table_state_col="STATE", value_col="value"):
    """Districts: see :func:`join_unit_values`."""
    return join_unit_values(boundaries, table, district_col, state_col, table_district_col, table_state_col, value_col)


def join_constituency_values(boundaries, table, constituency_col="pc_name", state_col="st_nm",
                             table_constituency_col="CONSTITUENCY", table_state_col="STATE", value_col="value"):
    """Parliamentary constituencies: see :func:`join_unit_values`."""
    return join_unit_values(boundaries, table, constituency_col, state_col, table_constituency_col, table_state_col, value_col)


def join_region(region, boundaries, table, value_col="value", **options):
    """Join your numbers for any region. Column names default to the region's spec.

    ``region`` is one of ``"states"``, ``"districts"``, ``"constituencies"``,
    ``"india_nepal_bhutan"``, ``"subcontinent"``. Pass ``name_col``,
    ``state_col``, ``table_name_col`` or ``table_state_col`` to override the
    column names; other options go to :func:`join_values` (``ladakh``,
    ``label_col``, ``extra_cols``, ``exclude``, ...).
    """
    spec = get_region(region)
    name_col = options.pop("name_col", spec.name_col)
    state_col = options.pop("state_col", spec.state_col)
    table_name_col = options.pop("table_name_col", spec.table_name_col)
    table_state_col = options.pop("table_state_col", spec.table_state_col)
    if spec.state_col:
        return join_unit_values(boundaries, table, name_col, state_col, table_name_col, table_state_col, value_col)
    options.setdefault("exclude", spec.exclude)
    return join_values(boundaries, table, name_col=name_col, table_name_col=table_name_col, value_col=value_col, **options)


def state_outlines(boundaries, state_col="st_nm"):
    """Dissolve districts into state shapes, to draw state borders over a district map."""
    return boundaries[[state_col, "geometry"]].dissolve(by=state_col).reset_index()
