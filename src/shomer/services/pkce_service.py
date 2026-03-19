# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""PKCE (Proof Key for Code Exchange) service per RFC 7636.

Provides code_verifier generation, code_challenge computation
(S256 and plain methods), and verification utilities.
"""

from __future__ import annotations

import base64
import hashlib
import secrets

#: Minimum length for a code_verifier per RFC 7636 §4.1.
MIN_VERIFIER_LENGTH = 43

#: Maximum length for a code_verifier per RFC 7636 §4.1.
MAX_VERIFIER_LENGTH = 128

#: Characters allowed in a code_verifier (unreserved URI characters).
_VERIFIER_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"


def generate_code_verifier(length: int = 128) -> str:
    """Generate a cryptographically random code_verifier.

    Parameters
    ----------
    length : int
        Length of the verifier (43–128 characters per RFC 7636 §4.1).

    Returns
    -------
    str
        A random string of unreserved URI characters.

    Raises
    ------
    ValueError
        If length is outside the 43–128 range.
    """
    if length < MIN_VERIFIER_LENGTH or length > MAX_VERIFIER_LENGTH:
        raise ValueError(
            f"code_verifier length must be {MIN_VERIFIER_LENGTH}-{MAX_VERIFIER_LENGTH}, "
            f"got {length}"
        )
    return "".join(secrets.choice(_VERIFIER_CHARS) for _ in range(length))


def compute_code_challenge(verifier: str, method: str = "S256") -> str:
    """Compute a code_challenge from a code_verifier.

    Parameters
    ----------
    verifier : str
        The code_verifier string.
    method : str
        Challenge method: ``S256`` (recommended) or ``plain``.

    Returns
    -------
    str
        The code_challenge value.

    Raises
    ------
    ValueError
        If the method is not ``S256`` or ``plain``.
    """
    if method == "plain":
        return verifier
    if method == "S256":
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    raise ValueError(f"Unsupported code_challenge_method: {method}")


def verify_code_challenge(verifier: str, challenge: str, method: str = "S256") -> bool:
    """Verify a code_verifier against a stored code_challenge.

    Parameters
    ----------
    verifier : str
        The code_verifier from the token request.
    challenge : str
        The code_challenge stored during the authorization request.
    method : str
        The method used to compute the challenge (``S256`` or ``plain``).

    Returns
    -------
    bool
        ``True`` if the verifier matches the challenge.

    Raises
    ------
    ValueError
        If the method is not ``S256`` or ``plain``.
    """
    computed = compute_code_challenge(verifier, method)
    return computed == challenge
