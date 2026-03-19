# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for OAuth2 scope description helper."""

from shomer.routes.oauth2 import _describe_scopes


class TestDescribeScopes:
    """Tests for _describe_scopes helper."""

    def test_known_scopes_have_descriptions(self) -> None:
        result = _describe_scopes(["openid", "profile", "email"])
        assert len(result) == 3
        assert result[0]["name"] == "openid"
        assert result[0]["description"] == "Verify your identity"
        assert result[1]["name"] == "profile"
        assert "profile information" in result[1]["description"]
        assert result[2]["name"] == "email"
        assert "email" in result[2]["description"]

    def test_unknown_scope_uses_name_as_description(self) -> None:
        result = _describe_scopes(["custom:read"])
        assert result[0]["name"] == "custom:read"
        assert result[0]["description"] == "custom:read"

    def test_empty_scopes(self) -> None:
        result = _describe_scopes([])
        assert result == []

    def test_mixed_known_and_unknown(self) -> None:
        result = _describe_scopes(["openid", "my_scope"])
        assert result[0]["description"] == "Verify your identity"
        assert result[1]["description"] == "my_scope"
