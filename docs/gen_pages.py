# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from pathlib import Path

import mkdocs_gen_files

FILES = {
    "CONTRIBUTING.md": "contributing.md",
    "CODE_OF_CONDUCT.md": "code_of_conduct.md",
    "CHANGELOG.md": "changelog.md",
    "LICENSE": "license.md",
}

for src_name, dest_name in FILES.items():
    src = Path(".") / src_name
    dest = Path(dest_name)

    try:
        content = src.read_text()

        # Add header for LICENSE
        if src_name == "LICENSE":
            content = f"# License\n\n```\n{content}\n```"

        with mkdocs_gen_files.open(dest, "w") as f:
            f.write(content)

    except FileNotFoundError:
        print(f"File {src} not found, skipping.")
    except Exception as e:
        print(f"An error occurred while processing {src}: {e}")
