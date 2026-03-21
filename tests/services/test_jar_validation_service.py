# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for JARValidationService."""

from __future__ import annotations

import json
import time
from typing import Any

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from shomer.services.jar_validation_service import (
    JARError,
    JARResult,
    JARValidationService,
)


def _generate_rsa_keypair() -> tuple[Any, dict[str, Any]]:
    """Generate an RSA keypair and return (private_key, jwks_dict)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Build JWK from public key
    from jwt.algorithms import RSAAlgorithm

    pub_jwk = json.loads(RSAAlgorithm.to_jwk(public_key))
    pub_jwk["kid"] = "test-kid"
    pub_jwk["use"] = "sig"
    pub_jwk["alg"] = "RS256"

    jwks = {"keys": [pub_jwk]}
    return private_key, jwks


def _sign_request_object(
    private_key: Any,
    claims: dict[str, Any],
    *,
    kid: str = "test-kid",
    algorithm: str = "RS256",
) -> str:
    """Sign a request object JWT."""
    return pyjwt.encode(
        claims,
        private_key,
        algorithm=algorithm,
        headers={"kid": kid},
    )


ISSUER = "https://auth.shomer.local"
CLIENT_ID = "test-client"


class TestJARValidationService:
    """Tests for JARValidationService.validate_request_object."""

    def test_valid_request_object(self) -> None:
        """Valid JWT request object returns extracted parameters."""
        private_key, jwks = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "response_type": "code",
            "redirect_uri": "https://app.example.com/cb",
            "scope": "openid",
            "state": "xyz",
            "nonce": "n1",
        }
        token = _sign_request_object(private_key, claims)
        svc = JARValidationService(ISSUER)
        result = svc.validate_request_object(
            request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
        )
        assert isinstance(result, JARResult)
        assert result.parameters["response_type"] == "code"
        assert result.parameters["redirect_uri"] == "https://app.example.com/cb"
        assert result.parameters["scope"] == "openid"
        assert result.parameters["state"] == "xyz"
        assert result.parameters["nonce"] == "n1"

    def test_extracts_pkce_params(self) -> None:
        """PKCE parameters are extracted from the request object."""
        private_key, jwks = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "response_type": "code",
            "code_challenge": "abc123",
            "code_challenge_method": "S256",
        }
        token = _sign_request_object(private_key, claims)
        svc = JARValidationService(ISSUER)
        result = svc.validate_request_object(
            request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
        )
        assert result.parameters["code_challenge"] == "abc123"
        assert result.parameters["code_challenge_method"] == "S256"

    def test_ignores_non_authorize_claims(self) -> None:
        """Non-authorization claims are not included in parameters."""
        private_key, jwks = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "response_type": "code",
            "custom_claim": "should_be_ignored",
            "iat": int(time.time()),
        }
        token = _sign_request_object(private_key, claims)
        svc = JARValidationService(ISSUER)
        result = svc.validate_request_object(
            request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
        )
        assert "custom_claim" not in result.parameters
        assert "iat" not in result.parameters
        assert "iss" not in result.parameters

    def test_malformed_jwt_raises_error(self) -> None:
        """Malformed JWT raises JARError."""
        svc = JARValidationService(ISSUER)
        with pytest.raises(JARError) as exc_info:
            svc.validate_request_object(
                request_jwt="not-a-jwt",
                client_id=CLIENT_ID,
                client_jwks={"keys": []},
            )
        assert exc_info.value.error == "invalid_request_object"
        assert "Malformed" in exc_info.value.description

    def test_wrong_issuer_raises_error(self) -> None:
        """iss != client_id raises JARError."""
        private_key, jwks = _generate_rsa_keypair()
        claims = {
            "iss": "wrong-client",
            "aud": ISSUER,
            "response_type": "code",
        }
        token = _sign_request_object(private_key, claims)
        svc = JARValidationService(ISSUER)
        with pytest.raises(JARError) as exc_info:
            svc.validate_request_object(
                request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
            )
        assert exc_info.value.error == "invalid_request_object"
        assert "iss" in exc_info.value.description

    def test_wrong_audience_raises_error(self) -> None:
        """aud != issuer raises JARError."""
        private_key, jwks = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": "https://wrong.issuer",
            "response_type": "code",
        }
        token = _sign_request_object(private_key, claims)
        svc = JARValidationService(ISSUER)
        with pytest.raises(JARError) as exc_info:
            svc.validate_request_object(
                request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
            )
        assert exc_info.value.error == "invalid_request_object"
        assert "aud" in exc_info.value.description

    def test_expired_token_raises_error(self) -> None:
        """Expired JWT raises JARError."""
        private_key, jwks = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "exp": int(time.time()) - 300,
            "response_type": "code",
        }
        token = _sign_request_object(private_key, claims)
        svc = JARValidationService(ISSUER)
        with pytest.raises(JARError) as exc_info:
            svc.validate_request_object(
                request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
            )
        assert exc_info.value.error == "invalid_request_object"
        assert "expired" in exc_info.value.description

    def test_invalid_signature_raises_error(self) -> None:
        """JWT signed with a different key raises JARError."""
        private_key, jwks = _generate_rsa_keypair()
        other_key, _ = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "response_type": "code",
        }
        # Sign with other_key but verify with original jwks
        token = _sign_request_object(other_key, claims)
        svc = JARValidationService(ISSUER)
        with pytest.raises(JARError) as exc_info:
            svc.validate_request_object(
                request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
            )
        assert exc_info.value.error == "invalid_request_object"
        assert "signature" in exc_info.value.description.lower()

    def test_empty_jwks_raises_error(self) -> None:
        """Empty JWKS raises JARError."""
        private_key, _ = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "response_type": "code",
        }
        token = _sign_request_object(private_key, claims)
        svc = JARValidationService(ISSUER)
        with pytest.raises(JARError) as exc_info:
            svc.validate_request_object(
                request_jwt=token,
                client_id=CLIENT_ID,
                client_jwks={"keys": []},
            )
        assert "no keys" in exc_info.value.description.lower()

    def test_no_matching_kid_raises_error(self) -> None:
        """JWT with kid not in JWKS raises JARError."""
        private_key, jwks = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "response_type": "code",
        }
        # Sign with a different kid
        token = _sign_request_object(private_key, claims, kid="other-kid")
        svc = JARValidationService(ISSUER)
        with pytest.raises(JARError) as exc_info:
            svc.validate_request_object(
                request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
            )
        assert "No matching key" in exc_info.value.description

    def test_client_id_extracted_as_parameter(self) -> None:
        """client_id in JWT payload is extracted as parameter."""
        private_key, jwks = _generate_rsa_keypair()
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "client_id": CLIENT_ID,
            "response_type": "code",
        }
        token = _sign_request_object(private_key, claims)
        svc = JARValidationService(ISSUER)
        result = svc.validate_request_object(
            request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
        )
        assert result.parameters["client_id"] == CLIENT_ID

    def test_key_without_kid_matches_when_jwt_has_no_kid(self) -> None:
        """Key without kid is used when JWT header has no kid."""
        private_key, jwks = _generate_rsa_keypair()
        # Remove kid from JWKS key
        del jwks["keys"][0]["kid"]
        claims = {
            "iss": CLIENT_ID,
            "aud": ISSUER,
            "response_type": "code",
        }
        # Sign without kid in header
        token = pyjwt.encode(claims, private_key, algorithm="RS256")
        svc = JARValidationService(ISSUER)
        result = svc.validate_request_object(
            request_jwt=token, client_id=CLIENT_ID, client_jwks=jwks
        )
        assert result.parameters["response_type"] == "code"


class TestAlgMatchesKty:
    """Tests for JARValidationService._alg_matches_kty."""

    def test_rs256_matches_rsa(self) -> None:
        assert JARValidationService._alg_matches_kty("RS256", "RSA") is True

    def test_ps256_matches_rsa(self) -> None:
        assert JARValidationService._alg_matches_kty("PS256", "RSA") is True

    def test_rs256_rejects_ec(self) -> None:
        assert JARValidationService._alg_matches_kty("RS256", "EC") is False

    def test_unknown_alg_rejects(self) -> None:
        assert JARValidationService._alg_matches_kty("ES256", "EC") is False
