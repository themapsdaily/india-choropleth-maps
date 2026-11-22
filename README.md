# India Choropleth Maps

Turn a simple table of numbers into a colour-shaded map of India. Pick states, districts or parliamentary constituencies, or draw India together with Nepal and Bhutan, or the whole of South Asia. Everything runs in Python, either on your computer or in Google Colab.

<!-- screenshot -->

## What you get

- A choropleth map where darker colours mean higher numbers, with grey for places that have no data.
- A matching colour bar and a ranked bar chart with rounded bars.
- An optional social card (an Instagram-style image) that puts the map, bar and your words together.
- A small web app, so you can try it without writing any code.

## Quick start

```bash
pip install "indiamaps @ git+https://github.com/themapsdaily/india-choropleth-maps.git"
```

```python
import pandas as pd
import indiamaps as im
from indiamaps import colors

boundaries = im.load_boundaries("india_states.geojson", name_col="st_nm")
table = pd.read_csv("examples/sample_state_values.csv", comment="#")  # columns: STATE, value
merged = im.join_region("states", boundaries, table)
cmap = im.build_custom_continuous_cmap(colors.white, colors.dodger_blue)
vmin, vmax = im.default_limits(merged["value"])
fig, ax = im.plot_region_map("states", merged, cmap, vmin, vmax, boundaries=boundaries, suffix="%")
im.save_figure(fig, "map.png", dpi=300, transparent=True)
```

The easiest way to learn it is to open a notebook in Colab (see the table below) and run it from top to bottom.

## Notebooks

| Notebook | What it makes | Open |
|---|---|---|
| `01_state_map` | States and union territories, with a Ladakh option (separate or merged into Jammu and Kashmir) | [Colab](https://colab.research.google.com/github/themapsdaily/india-choropleth-maps/blob/main/notebooks/01_state_map.ipynb) |
| `02_district_map` | Districts, with state borders on top and top and bottom bar charts | [Colab](https://colab.research.google.com/github/themapsdaily/india-choropleth-maps/blob/main/notebooks/02_district_map.ipynb) |
| `03_constituency_map` | Lok Sabha constituencies, matched on constituency and state | [Colab](https://colab.research.google.com/github/themapsdaily/india-choropleth-maps/blob/main/notebooks/03_constituency_map.ipynb) |
| `04_india_nepal_bhutan_map` | Indian states with Nepal and Bhutan as single shapes | [Colab](https://colab.research.google.com/github/themapsdaily/india-choropleth-maps/blob/main/notebooks/04_india_nepal_bhutan_map.ipynb) |
| `05_subcontinent_map` | The first-level divisions of every country in South Asia | [Colab](https://colab.research.google.com/github/themapsdaily/india-choropleth-maps/blob/main/notebooks/05_subcontinent_map.ipynb) |

Each notebook has one settings cell at the top (colour, numbers shown, scale) and plain-language text before every step.

## Bring your own map

This repository does not include any boundary files. Maps of India involve official borders that differ between sources, so you choose the file and take responsibility for how the borders are shown. Good places to look:

- [DataMeet community maps](https://github.com/datameet/maps), free maps of India made by volunteers.
- The Survey of India, whose published boundary is the official one for maps of India published in India.
- Your own file from QGIS or any other tool.

Check the licence of whatever file you pick before you publish a map made from it.

Each region reads these columns:

| Region | Boundary file needs | Your table needs |
|---|---|---|
| `states` | `st_nm` | `STATE`, `value` |
| `districts` | `dt_nm`, `st_nm` | `DISTRICT`, `STATE`, `value` |
| `constituencies` | `pc_name`, `st_nm` | `CONSTITUENCY`, `STATE`, `value` |
| `india_nepal_bhutan` | `st_nm` | `STATE`, `value` |
| `subcontinent` | `st_nm` | `STATE`, `value` |

If your file uses other column names, pass `name_col=` and `state_col=` to the functions. Names are matched ignoring capital letters and punctuation, and anything that does not match is reported so you can fix the spelling. Example tables with made-up numbers are in `examples/`.

## Colours

The colour scale runs from white to a colour you pick. `indiamaps.colors` has a set of named colours (`dodger_blue`, `persian_green`, `radical_red` and more), and any `[R, G, B]` list works. To blend through several colours, give them all to `build_custom_continuous_cmap`.

## Fonts

Text uses the default font that ships with matplotlib. For a different look, pass the path to any `.ttf` or `.otf` file as `font_path`. The free [Inter](https://rsms.me/inter/) font works well. We do not bundle fonts, because most good ones have licences that stop redistribution.

## Run it in the browser

```bash
git clone https://github.com/themapsdaily/india-choropleth-maps.git
cd india-choropleth-maps
pip install -e ".[app]"
streamlit run app/streamlit_app.py
```

Upload your boundary file and your table, choose a region and a colour, and download the map.

## Status

This code grew from a set of notebooks we used between 2022 and 2025 to make maps for TheMapsDaily. It has been cleaned up and turned into a package, but it is still young: expect rough edges, and please open an issue if something breaks. The earliest versions of the notebooks are kept in `archive/` for history.

## Licence

MIT, see `LICENSE`. You may use the code for anything, including commercial work. If you publish maps made with it, a credit to TheMapsDaily is appreciated but not required.

Made by [TheMapsDaily](https://themapsdaily.com).
