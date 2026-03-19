# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for PKCE service (RFC 7636)."""

from __future__ import annotations

import base64
import hashlib

import pytest

from shomer.services.pkce_service import (
    MAX_VERIFIER_LENGTH,
    MIN_VERIFIER_LENGTH,
    compute_code_challenge,
    generate_code_verifier,
    verify_code_challenge,
)


class TestGenerateCodeVerifier:
    """Tests for generate_code_verifier()."""

    def test_default_length(self) -> None:
        """Default verifier is 128 characters."""
        v = generate_code_verifier()
        assert len(v) == 128

    def test_custom_length(self) -> None:
        """Custom length is respected."""
        v = generate_code_verifier(64)
        assert len(v) == 64

    def test_min_length(self) -> None:
        """Minimum allowed length (43)."""
        v = generate_code_verifier(MIN_VERIFIER_LENGTH)
        assert len(v) == 43

    def test_max_length(self) -> None:
        """Maximum allowed length (128)."""
        v = generate_code_verifier(MAX_VERIFIER_LENGTH)
        assert len(v) == 128

    def test_too_short_raises(self) -> None:
        """Length below 43 raises ValueError."""
        with pytest.raises(ValueError, match="43-128"):
            generate_code_verifier(42)

    def test_too_long_raises(self) -> None:
        """Length above 128 raises ValueError."""
        with pytest.raises(ValueError, match="43-128"):
            generate_code_verifier(129)

    def test_uses_unreserved_chars(self) -> None:
        """Generated verifier only contains unreserved URI characters."""
        allowed = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
        )
        v = generate_code_verifier()
        assert set(v).issubset(allowed)

    def test_randomness(self) -> None:
        """Multiple verifiers are different."""
        verifiers = {generate_code_verifier() for _ in range(10)}
        assert len(verifiers) == 10


class TestComputeCodeChallenge:
    """Tests for compute_code_challenge()."""

    def test_s256(self) -> None:
        """S256 computes SHA-256 + base64url-no-pad."""
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        expected_digest = hashlib.sha256(verifier.encode("ascii")).digest()
        expected = (
            base64.urlsafe_b64encode(expected_digest).rstrip(b"=").decode("ascii")
        )
        assert compute_code_challenge(verifier, "S256") == expected

    def test_plain(self) -> None:
        """Plain returns the verifier as-is."""
        verifier = "my-plain-verifier"
        assert compute_code_challenge(verifier, "plain") == verifier

    def test_unsupported_method_raises(self) -> None:
        """Unsupported method raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported"):
            compute_code_challenge("verifier", "RS256")


class TestVerifyCodeChallenge:
    """Tests for verify_code_challenge()."""

    def test_s256_valid(self) -> None:
        """Correct S256 verifier returns True."""
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        challenge = compute_code_challenge(verifier, "S256")
        assert verify_code_challenge(verifier, challenge, "S256") is True

    def test_s256_invalid(self) -> None:
        """Wrong S256 verifier returns False."""
        challenge = compute_code_challenge("correct-verifier", "S256")
        assert verify_code_challenge("wrong-verifier", challenge, "S256") is False

    def test_plain_valid(self) -> None:
        """Correct plain verifier returns True."""
        assert verify_code_challenge("verifier", "verifier", "plain") is True

    def test_plain_invalid(self) -> None:
        """Wrong plain verifier returns False."""
        assert verify_code_challenge("verifier", "wrong", "plain") is False

    def test_unsupported_method_raises(self) -> None:
        """Unsupported method raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported"):
            verify_code_challenge("v", "c", "unknown")

    def test_roundtrip_s256(self) -> None:
        """Generate → compute → verify roundtrip works."""
        verifier = generate_code_verifier()
        challenge = compute_code_challenge(verifier, "S256")
        assert verify_code_challenge(verifier, challenge, "S256") is True

    def test_roundtrip_plain(self) -> None:
        """Generate → compute → verify roundtrip works for plain."""
        verifier = generate_code_verifier()
        challenge = compute_code_challenge(verifier, "plain")
        assert verify_code_challenge(verifier, challenge, "plain") is True
