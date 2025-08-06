# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Command-line interface for the Shomer authentication service."""

import argparse

from shomer import __version__


def main() -> None:
    """Parse command-line arguments and execute the CLI."""
    parser = argparse.ArgumentParser(
        prog="shomer", description="OIDC/OAuth2 authentication service."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s v{__version__}"
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
