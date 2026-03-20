# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OIDC ID Token generation service.

Builds ID Tokens with required claims (iss, sub, aud, exp, iat),
optional nonce and auth_time, and profile claims based on requested
scopes per OpenID Connect Core 1.0 §2 and §5.1.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from shomer.core.settings import Settings
from shomer.models.user_profile import UserProfile

#: Map of OIDC scope → profile claim fields to include.
_SCOPE_CLAIMS: dict[str, list[str]] = {
    "profile": [
        "name",
        "given_name",
        "family_name",
        "middle_name",
        "nickname",
        "preferred_username",
        "profile",
        "picture",
        "website",
        "gender",
        "birthdate",
        "zoneinfo",
        "locale",
    ],
    "email": ["email", "email_verified"],
    "address": ["address"],
    "phone": ["phone_number", "phone_number_verified"],
}


class IDTokenService:
    """Generate OIDC ID Tokens with standard claims.

    Attributes
    ----------
    settings : Settings
        Application settings (issuer, expiration, signing key).
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_id_token(
        self,
        *,
        sub: str,
        aud: str,
        nonce: str | None = None,
        auth_time: datetime | None = None,
        scopes: list[str] | None = None,
        profile: UserProfile | None = None,
        email: str | None = None,
        email_verified: bool = False,
    ) -> str:
        """Build and sign an OIDC ID Token.

        Parameters
        ----------
        sub : str
            Subject identifier (user ID).
        aud : str
            Audience (client_id).
        nonce : str or None
            Nonce from the authorization request (included if present).
        auth_time : datetime or None
            Time of user authentication (included if present).
        scopes : list[str] or None
            Requested scopes — determines which profile claims to include.
        profile : UserProfile or None
            User profile for claim population.
        email : str or None
            User email address (for ``email`` scope).
        email_verified : bool
            Whether the email is verified (for ``email`` scope).

        Returns
        -------
        str
            Signed JWT ID Token.
        """
        import jwt as pyjwt

        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "iss": self.settings.jwt_issuer,
            "sub": sub,
            "aud": aud,
            "exp": now + timedelta(seconds=self.settings.jwt_id_token_exp),
            "iat": now,
        }

        if nonce:
            payload["nonce"] = nonce

        if auth_time is not None:
            payload["auth_time"] = int(auth_time.timestamp())

        # Add profile claims based on scopes
        requested_scopes = set(scopes or [])
        if "email" in requested_scopes and email:
            payload["email"] = email
            payload["email_verified"] = email_verified

        if "profile" in requested_scopes and profile is not None:
            payload.update(self._extract_profile_claims(profile))

        if "address" in requested_scopes and profile is not None:
            address = self._extract_address_claims(profile)
            if address:
                payload["address"] = address

        if "phone" in requested_scopes and profile is not None:
            if profile.phone_number:
                payload["phone_number"] = profile.phone_number
                payload["phone_number_verified"] = profile.phone_number_verified

        return pyjwt.encode(
            payload,
            self.settings.jwk_encryption_key or "dev-secret",
            algorithm="HS256",
        )

    @staticmethod
    def _extract_profile_claims(profile: UserProfile) -> dict[str, Any]:
        """Extract standard profile claims from a UserProfile.

        Parameters
        ----------
        profile : UserProfile
            The user profile.

        Returns
        -------
        dict[str, Any]
            Non-None profile claims.
        """
        claims: dict[str, Any] = {}
        field_map = {
            "name": "name",
            "given_name": "given_name",
            "family_name": "family_name",
            "middle_name": "middle_name",
            "nickname": "nickname",
            "preferred_username": "preferred_username",
            "profile": "profile_url",
            "picture": "picture_url",
            "website": "website",
            "gender": "gender",
            "birthdate": "birthdate",
            "zoneinfo": "zoneinfo",
            "locale": "locale",
        }
        for claim_name, attr_name in field_map.items():
            value = getattr(profile, attr_name, None)
            if value is not None:
                claims[claim_name] = value
        return claims

    @staticmethod
    def _extract_address_claims(profile: UserProfile) -> dict[str, str] | None:
        """Extract OIDC address claim from a UserProfile.

        Parameters
        ----------
        profile : UserProfile
            The user profile.

        Returns
        -------
        dict[str, str] or None
            Address object per OIDC Core §5.1.1, or None if no address data.
        """
        address: dict[str, str] = {}
        if profile.address_formatted:
            address["formatted"] = profile.address_formatted
        if profile.address_street:
            address["street_address"] = profile.address_street
        if profile.address_locality:
            address["locality"] = profile.address_locality
        if profile.address_region:
            address["region"] = profile.address_region
        if profile.address_postal_code:
            address["postal_code"] = profile.address_postal_code
        if profile.address_country:
            address["country"] = profile.address_country
        return address or None
