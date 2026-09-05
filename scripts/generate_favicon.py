#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Convert an SVG file to a multi-resolution favicon.ico."""

import argparse
import io
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "assets" / "shomer.svg"
DEFAULT_OUTPUT = ROOT / "docs" / "favicon.ico"


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert an SVG file to favicon.ico")
    parser.add_argument(
        "-i", "--input", type=Path, default=DEFAULT_INPUT, help="Input SVG file"
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_OUTPUT, help="Output ICO file"
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Rasterise once at 256px and let Pillow downsample: rendering each
    # size from the SVG separately produces subtly different hinting
    # between them, which shows up as a "wobbly" icon in the tab strip.
    png_data = cairosvg.svg2png(
        url=str(args.input), output_width=256, output_height=256
    )
    img = Image.open(io.BytesIO(png_data))
    img.save(str(args.output), format="ICO", sizes=[(48, 48), (32, 32), (16, 16)])
    print(f"Favicon generated: {args.output}")


if __name__ == "__main__":
    main()
