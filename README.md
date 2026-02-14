# Crosshatch

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/joeljose/Crosshatch/blob/main/crosshatch.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<img src="assets/output/crosshatch_example.jpg" alt="Crosshatch Example" width="800"/>

Turn portrait photos into crosshatch drawings using automatic segmentation and hatch pattern blending.

## What is Crosshatching?

Crosshatching is a drawing technique where layers of parallel lines are overlaid at different angles to create tonal effects. Artists use denser, overlapping hatches for dark areas and sparse hatches for light areas. This project automates that process: segment the subject, analyze its tonal range, and map hatch textures onto different brightness zones.

## How It Works

1. **Segment** the subject from the background using SAM2
2. **Resize** the image to match the hatch texture dimensions
3. **Layer** the subject onto a white background
4. **Analyze** the tonal range via histogram and compute threshold boundaries
5. **Apply** a different hatch pattern to each tonal region
6. **Blend** the hatch layers into the final crosshatch drawing

## How to Use

1. Click the **"Open in Colab"** badge above
2. Run all cells
3. Upload your portrait
4. Download the result

## Hatch Styles

| Style | Description |
|-------|-------------|
| **Horizontal** | Classic parallel lines — clean, traditional look |
| **Vortex** | Circular swirl pattern — more artistic and dynamic |

## Follow Me

<a href="https://twitter.com/joelk1jose" target="_blank"><img src="assets/icons/tw.png" width="30"></a>
<a href="https://github.com/joeljose" target="_blank"><img src="assets/icons/gthb.png" width="30"></a>
<a href="https://www.linkedin.com/in/joel-jose-527b80102/" target="_blank"><img src="assets/icons/lnkdn.png" width="30"></a>

## License

[MIT](LICENSE)
