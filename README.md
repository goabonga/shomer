<div align="center">
  <img src="assets/shomer.svg" alt="Shomer" width="120" />

  <h1>Shomer</h1>

  <p><strong>Shomer</strong> (<em>שׁוֹמֵר</em>) is Hebrew for <em>guardian</em>,
  <em>watchman</em> — the one who keeps watch over the gate.</p>

  <p>Shomer is an <strong>OpenID Connect / OAuth 2.0</strong> platform.</p>

  [![ci](https://github.com/goabonga/shomer/actions/workflows/ci.yml/badge.svg)](https://github.com/goabonga/shomer/actions/workflows/ci.yml)
  [![docs](https://img.shields.io/badge/docs-github.io-blue)](https://goabonga.github.io/shomer/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
  [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
</div>

---

## Documentation

The full documentation is published at
**[goabonga.github.io/shomer](https://goabonga.github.io/shomer/)**.

## Packages

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/). Every package is versioned, changelogged,
tagged and released on its own.

| Package | Kind | What it is |
| --- | --- | --- |

## Requirements

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/)

## Getting started

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer

uv sync --all-packages

```

## Versioning and releases

Versions are not edited by hand. [multicz](https://github.com/goabonga/multicz)
reads the [Conventional Commits](https://www.conventionalcommits.org/) since
each component's last tag, decides the bump, writes the changelog and tags
the release. On every push to `main`, CI bumps everything that changed in
one commit and publishes each component from its own job.

Which component a commit releases is decided by the paths it touches — see
`paths` in [multicz.toml](multicz.toml).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports go through
[SECURITY.md](SECURITY.md), not the public tracker.

## License

[MIT](LICENSE) © 2026 Chris
