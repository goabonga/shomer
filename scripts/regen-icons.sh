#!/usr/bin/env bash

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

#
# Regenerate every derived icon from the canonical SVG at
# `assets/shomer.svg`. Re-run after editing the master SVG.
#
# Favicon generation delegates to `scripts/generate_favicon.py`
# (cairosvg + Pillow), pinned in the workspace's `favicon` dep group.

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$ROOT/assets/shomer.svg"

if [[ ! -f "$SRC" ]]; then
  echo "regen-icons: missing $SRC" >&2
  exit 1
fi

# Docs site logo — zensical reads `docs/shomer.svg`.
mkdir -p "$ROOT/docs"
cp "$SRC" "$ROOT/docs/shomer.svg"

# Docs favicon.
uv run --group favicon python "$ROOT/scripts/generate_favicon.py" \
  -i "$SRC" \
  -o "$ROOT/docs/favicon.ico"

# The favicon served at /favicon.ico by the ssr.
#
# It lives in static/ next to the esbuild output rather than in a
# directory of its own: that path is already on the /static mount,
# already inside `packages = ["src/shomer_ssr"]` so the wheel picks it
# up, and already tracked. The web build writes main.js/main.css there
# and removes only .html files from templates/, so it will not be swept
# away.
mkdir -p "$ROOT/packages/ssr/src/shomer_ssr/static"
uv run --group favicon python "$ROOT/scripts/generate_favicon.py" \
  -i "$SRC" \
  -o "$ROOT/packages/ssr/src/shomer_ssr/static/favicon.ico"

echo "regen-icons: docs/shomer.svg + docs/favicon.ico + ssr favicon.ico from $SRC"
