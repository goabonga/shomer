# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the environment-resolved settings."""

import pytest

from shomer_lib.settings import DEFAULT_DATABASE_URL, DEFAULT_ISSUER, EnvSettings


def test_defaults_apply_when_nothing_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SHOMER_ISSUER", raising=False)
    monkeypatch.delenv("SHOMER_DATABASE_URL", raising=False)
    settings = EnvSettings.from_env()
    assert settings.issuer == DEFAULT_ISSUER
    assert settings.database_url == DEFAULT_DATABASE_URL


def test_environment_overrides_the_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOMER_ISSUER", "https://id.example.test")
    monkeypatch.setenv("SHOMER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    settings = EnvSettings.from_env()
    assert settings.issuer == "https://id.example.test"
    assert settings.database_url == "sqlite+pysqlite:///:memory:"


def test_issuer_loses_its_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    # `iss` is compared byte for byte by every conforming client, and the
    # discovery URLs are built by concatenation — one stray slash is the
    # difference between a token that validates and one that does not.
    monkeypatch.setenv("SHOMER_ISSUER", "https://id.example.test/")
    assert EnvSettings.from_env().issuer == "https://id.example.test"


def test_a_custom_prefix_is_honoured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTHER_ISSUER", "https://other.example.test")
    assert EnvSettings.from_env("OTHER_").issuer == "https://other.example.test"


def test_settings_are_frozen() -> None:
    with pytest.raises(AttributeError):
        EnvSettings().issuer = "nope"  # type: ignore[misc]
