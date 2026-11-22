import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from PIL import Image

import indiamaps as im


def _setup(squares, table):
    merged = im.join_values(squares, table)
    cmap = im.build_custom_continuous_cmap(im.colors.white, im.colors.dodger_blue)
    return merged, cmap


def test_map_renders_to_png(squares, table, tmp_path):
    merged, cmap = _setup(squares, table)
    fig, ax = im.plot_state_map(merged, cmap, 0, 40, suffix="%", figsize=(6, 6))
    out = tmp_path / "map.png"
    im.save_figure(fig, out, dpi=60, transparent=True)
    plt.close(fig)
    assert Image.open(out).size == (360, 360)


def test_no_data_region_is_grey(squares, table):
    merged, cmap = _setup(squares, table)
    fig, ax = im.plot_choropleth(merged, cmap, 0, 40, figsize=(4, 4))
    fig.canvas.draw()
    # Goa has no number; its patch colour must be the grey fill.
    grey = tuple(round(c, 2) for c in im.maps.NO_DATA_COLOR[:3])
    assert grey in {tuple(round(c, 2) for c in fc[:3]) for fc in ax.collections[0].get_facecolor()}
    plt.close(fig)


def test_label_modes(squares, table):
    merged, cmap = _setup(squares, table)
    merged["custom"] = "x"
    for mode in ("int", "float", "custom", "na"):
        fig, ax = im.plot_choropleth(merged, cmap, 0, 40, figsize=(4, 4))
        im.add_labels(ax, merged, mode=mode, digits=1, suffix="%")
        plt.close(fig)


def test_chart_and_colorbar_render(squares, table, tmp_path):
    merged, cmap = _setup(squares, table)
    bar = im.colorbar(0, 40, cmap)
    im.save_figure(bar, tmp_path / "bar.png", dpi=30)
    plt.close(bar)
    for which in ("all", "top", "bottom", "middle"):
        fig, ax = im.ranked_bar_chart(merged, im.colors.dodger_blue, which=which, n=2, figsize=(5, 5), suffix="%")
        plt.close(fig)
    fig, ax = im.ranked_bar_chart(merged, "dodger_blue", figsize=(5, 5))
    labels = [t.get_text() for t in ax.get_yticklabels()]
    assert labels[0] == "Kerala" and "Goa" not in labels  # ranked, missing data left out
    plt.close(fig)
    assert (tmp_path / "bar.png").stat().st_size > 0


def test_short_names_on_bar_axis(squares, table):
    merged, cmap = _setup(squares, table)
    fig, ax = im.ranked_bar_chart(merged, "dodger_blue", figsize=(5, 5))
    labels = [t.get_text() for t in ax.get_yticklabels()]
    assert "Jammu & Kashmir" in labels
    plt.close(fig)


def test_card_renders(squares, table, tmp_path):
    merged, cmap = _setup(squares, table)
    fig, ax = im.plot_state_map(merged, cmap, 0, 40, figsize=(6, 6))
    im.save_figure(fig, tmp_path / "map.png", dpi=40, transparent=True)
    plt.close(fig)
    bar = im.colorbar(0, 40, cmap)
    im.save_figure(bar, tmp_path / "cb.png", dpi=40)
    plt.close(bar)
    text = im.CardText(header_1="A TITLE", header_2="HERE", scale_min="0", scale_max="40")
    card = im.map_card(tmp_path / "map.png", tmp_path / "cb.png", text)
    assert card.size == (4000, 4000)
