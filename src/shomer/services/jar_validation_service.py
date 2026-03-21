# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""JAR (JWT-Secured Authorization Request) validation service per RFC 9101."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from jwt.algorithms import RSAAlgorithm


class JARError(Exception):
    """Raised when a JAR request object validation fails.

    Attributes
    ----------
    error : str
        OAuth2 error code per RFC 9101.
    description : str
        Human-readable error description.
    """

    def __init__(self, error: str, description: str) -> None:
        self.error = error
        self.description = description
        super().__init__(description)


@dataclass(frozen=True)
class JARResult:
    """Result of a successful JAR request object validation.

    Attributes
    ----------
    parameters : dict[str, Any]
        Authorization parameters extracted from the JWT payload.
    """

    parameters: dict[str, Any]


class JARValidationService:
    """Validate JWT Request Objects per RFC 9101.

    Verifies the JWT signature using the client's registered JWKS,
    validates claims (``iss`` must equal ``client_id``, ``aud`` must
    equal the authorization server issuer), and extracts the
    authorization parameters from the payload.

    Attributes
    ----------
    issuer : str
        The authorization server's issuer identifier.
    """

    #: Authorization parameters that can appear in a JAR request object.
    _AUTHORIZE_PARAMS: set[str] = {
        "client_id",
        "redirect_uri",
        "response_type",
        "scope",
        "state",
        "nonce",
        "prompt",
        "login_hint",
        "code_challenge",
        "code_challenge_method",
    }

    def __init__(self, issuer: str) -> None:
        self.issuer = issuer

    def validate_request_object(
        self,
        *,
        request_jwt: str,
        client_id: str,
        client_jwks: dict[str, Any],
    ) -> JARResult:
        """Parse and validate a JWT request object.

        Parameters
        ----------
        request_jwt : str
            The encoded JWT request object.
        client_id : str
            The client_id that must match the ``iss`` claim.
        client_jwks : dict[str, Any]
            The client's JWKS (JSON Web Key Set) containing public keys
            for signature verification. Must have a ``keys`` array.

        Returns
        -------
        JARResult
            The extracted authorization parameters.

        Raises
        ------
        JARError
            If the JWT is malformed, the signature is invalid, or
            claims validation fails.
        """
        # 1. Parse JWT header
        try:
            header = jwt.get_unverified_header(request_jwt)
        except jwt.exceptions.DecodeError as exc:
            raise JARError(
                "invalid_request_object", "Malformed JWT request object"
            ) from exc

        alg = header.get("alg", "RS256")
        kid = header.get("kid")

        # 2. Find the signing key from the client's JWKS
        public_key = self._find_key(client_jwks, kid=kid, alg=alg)

        # 3. Verify signature and decode claims
        try:
            claims = jwt.decode(
                request_jwt,
                public_key,
                algorithms=[alg],
                issuer=client_id,
                audience=self.issuer,
            )
        except jwt.ExpiredSignatureError as exc:
            raise JARError(
                "invalid_request_object", "Request object has expired"
            ) from exc
        except jwt.InvalidSignatureError as exc:
            raise JARError(
                "invalid_request_object", "Invalid request object signature"
            ) from exc
        except jwt.InvalidIssuerError as exc:
            raise JARError(
                "invalid_request_object",
                f"iss claim must equal client_id ({client_id})",
            ) from exc
        except jwt.InvalidAudienceError as exc:
            raise JARError(
                "invalid_request_object",
                f"aud claim must equal issuer ({self.issuer})",
            ) from exc
        except jwt.DecodeError as exc:
            raise JARError(
                "invalid_request_object", "Failed to decode request object"
            ) from exc

        # 4. Validate required claims per RFC 9101 §4
        if "iss" not in claims:
            raise JARError("invalid_request_object", "Missing iss claim")
        if "aud" not in claims:
            raise JARError("invalid_request_object", "Missing aud claim")

        # 5. Extract authorization parameters
        parameters: dict[str, Any] = {}
        for param in self._AUTHORIZE_PARAMS:
            if param in claims:
                parameters[param] = claims[param]

        return JARResult(parameters=parameters)

    def _find_key(
        self,
        jwks: dict[str, Any],
        *,
        kid: str | None,
        alg: str,
    ) -> Any:
        """Find a public key in a JWKS by kid and algorithm.

        Parameters
        ----------
        jwks : dict[str, Any]
            JSON Web Key Set with a ``keys`` array.
        kid : str or None
            Key ID from the JWT header. If ``None``, uses the first
            matching key.
        alg : str
            Expected algorithm (e.g. ``RS256``).

        Returns
        -------
        RSAPublicKey
            The public key for verification.

        Raises
        ------
        JARError
            If no matching key is found.
        """
        keys = jwks.get("keys", [])
        if not keys:
            raise JARError("invalid_request_object", "Client JWKS contains no keys")

        for key_data in keys:
            key_alg = key_data.get("alg", alg)
            key_kid = key_data.get("kid")
            key_use = key_data.get("use", "sig")

            # Match by kid if provided
            if kid and key_kid and kid != key_kid:
                continue

            # Skip encryption keys
            if key_use != "sig":
                continue

            # Match algorithm family
            if not self._alg_matches_kty(key_alg, key_data.get("kty", "")):
                continue

            try:
                return RSAAlgorithm.from_jwk(key_data)
            except Exception as exc:  # noqa: BLE001
                raise JARError(
                    "invalid_request_object",
                    f"Failed to load key from JWKS: {exc}",
                ) from exc

        raise JARError(
            "invalid_request_object",
            f"No matching key found in client JWKS (kid={kid}, alg={alg})",
        )

    @staticmethod
    def _alg_matches_kty(alg: str, kty: str) -> bool:
        """Check if an algorithm is compatible with a key type.

        Parameters
        ----------
        alg : str
            JWT algorithm (e.g. ``RS256``).
        kty : str
            JWK key type (e.g. ``RSA``).

        Returns
        -------
        bool
            Whether the algorithm and key type are compatible.
        """
        rsa_algs = {"RS256", "RS384", "RS512", "PS256", "PS384", "PS512"}
        if alg in rsa_algs:
            return kty == "RSA"
        return False
