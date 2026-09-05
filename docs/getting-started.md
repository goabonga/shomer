---
icon: lucide/rocket
---

# Getting started

## Requirements

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/)

## Clone and install

```bash
git clone https://github.com/goabonga/shomer.git
cd shomer

uv sync --all-packages   # Python packages + dev tooling
```

## The gates

These are exactly what CI runs; running them locally is the only way to
find out before the pipeline does.

```bash
```

Install the hooks once and most of it runs on commit:

```bash
uv run pre-commit install
```
