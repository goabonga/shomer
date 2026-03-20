# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OIDC Discovery endpoint per OpenID Connect Discovery 1.0.

Returns the server configuration document at
``/.well-known/openid-configuration``.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from shomer.core.settings import get_settings

router = APIRouter()

#: Cache-Control max-age for the discovery document (seconds).
DISCOVERY_CACHE_MAX_AGE = 3600


@router.get("/.well-known/openid-configuration")
async def openid_configuration() -> JSONResponse:
    """Return the OIDC Discovery document.

    Provides client auto-discovery of the server's capabilities
    per OpenID Connect Discovery 1.0 §3.

    Returns
    -------
    JSONResponse
        JSON discovery document with Cache-Control header.
    """
    settings = get_settings()
    issuer = settings.jwt_issuer

    config: dict[str, Any] = {
        # Required
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/oauth2/authorize",
        "token_endpoint": f"{issuer}/oauth2/token",
        "userinfo_endpoint": f"{issuer}/userinfo",
        "jwks_uri": f"{issuer}/.well-known/jwks.json",
        # Recommended
        "registration_endpoint": None,
        "scopes_supported": [
            "openid",
            "profile",
            "email",
            "address",
            "phone",
            "offline_access",
        ],
        "response_types_supported": ["code"],
        "response_modes_supported": ["query"],
        "grant_types_supported": [
            "authorization_code",
            "client_credentials",
            "password",
            "refresh_token",
        ],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256", "RS256"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
            "none",
        ],
        "claims_supported": [
            "sub",
            "iss",
            "aud",
            "exp",
            "iat",
            "nonce",
            "auth_time",
            "name",
            "given_name",
            "family_name",
            "nickname",
            "preferred_username",
            "profile",
            "picture",
            "website",
            "email",
            "email_verified",
            "gender",
            "birthdate",
            "zoneinfo",
            "locale",
            "phone_number",
            "phone_number_verified",
            "address",
        ],
        "code_challenge_methods_supported": ["S256", "plain"],
        # Additional endpoints
        "revocation_endpoint": f"{issuer}/oauth2/revoke",
        "introspection_endpoint": f"{issuer}/oauth2/introspect",
        "end_session_endpoint": f"{issuer}/auth/logout",
    }

    return JSONResponse(
        content=config,
        headers={"Cache-Control": f"public, max-age={DISCOVERY_CACHE_MAX_AGE}"},
    )
