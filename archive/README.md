# Archive

These two notebooks are the earliest versions of the code, kept for history. They are not meant to be run as they are: they read files that are not in this repository (a boundary shapefile, an Excel sheet, a background image and fonts), and the first cell of each used to mount Google Drive, which has been removed. Use the notebooks in `../notebooks` instead.

| File | What it was |
| --- | --- |
| `2022_first_version.ipynb` | One long notebook: everything, including the colour bar and the Instagram card, written out in full in the cells. The figures are drawn smaller than in later versions. |
| `2023_second_version.ipynb` | The same idea at full size. Adds the blue, white and red scale for numbers that go below and above zero, optional text on the map, and the second card with the bar chart. |

What changed in the package that replaced them:

- The plotting helpers became the `indiamaps` package, so a notebook is now a short list of steps instead of hundreds of lines.
- Hand-typed label positions in a spreadsheet became positions worked out from the shapes.
- Paths, fonts and background images became arguments, with a plain default font.
- Several choices that used to be commented out and back in (even or power scale, whole numbers or decimals, Ladakh joined or separate) became options.

Outputs have been stripped and every private path and key has been removed.
