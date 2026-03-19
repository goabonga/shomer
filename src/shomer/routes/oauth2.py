# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OAuth2 endpoints."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from shomer.deps import DbSession
from shomer.services.authorize_service import AuthorizeError, AuthorizeService
from shomer.services.session_service import SessionService

router = APIRouter(prefix="/oauth2", tags=["oauth2"])


@router.get("/authorize")
async def authorize(
    request: Request,
    db: DbSession,
    client_id: str | None = None,
    redirect_uri: str | None = None,
    response_type: str | None = None,
    scope: str | None = None,
    state: str | None = None,
    nonce: str | None = None,
    prompt: str | None = None,
    login_hint: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
) -> RedirectResponse:
    """OAuth2 authorization endpoint per RFC 6749 §4.1.1.

    Validates the request, checks authentication, and either redirects
    to login, shows consent, or issues an authorization code.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Injected async database session.
    client_id : str or None
        OAuth2 client identifier.
    redirect_uri : str or None
        Requested redirect URI.
    response_type : str or None
        Must be ``code``.
    scope : str or None
        Requested scopes.
    state : str or None
        CSRF state parameter.
    nonce : str or None
        OIDC nonce.
    prompt : str or None
        OIDC prompt parameter.
    login_hint : str or None
        OIDC login hint.
    code_challenge : str or None
        PKCE code challenge.
    code_challenge_method : str or None
        PKCE challenge method.

    Returns
    -------
    RedirectResponse
        Redirect to login, consent, or callback with code.
    """
    svc = AuthorizeService(db)

    # Validate request parameters
    try:
        auth_request = await svc.validate_request(
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope,
            state=state,
            nonce=nonce,
            prompt=prompt,
            login_hint=login_hint,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
    except AuthorizeError as exc:
        # OWASP: NEVER redirect to an unvalidated redirect_uri.
        # Only redirect with error if the redirect_uri was already
        # verified against the client's registered URIs. Since
        # validate_request() raises before we reach that point for
        # client_id/redirect_uri errors, we always return 400 here.
        # The only errors that could occur AFTER redirect_uri validation
        # (response_type, scope, state) are safe to redirect.
        safe_redirect = exc.error in (
            "unsupported_response_type",
            "unauthorized_client",
        )
        if safe_redirect and redirect_uri and state:
            params = {
                "error": exc.error,
                "error_description": exc.description,
                "state": state,
            }
            return RedirectResponse(
                url=f"{redirect_uri}?{urlencode(params)}", status_code=302
            )
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.error, "error_description": exc.description},
        )

    # Check if user is authenticated
    session_token = request.cookies.get("session_id")
    session_svc = SessionService(db)
    session = None
    if session_token:
        session = await session_svc.validate(session_token)

    if session is None or prompt == "login":
        # Redirect to login with return URL (URL-encoded to prevent injection)
        from urllib.parse import quote

        authorize_url = quote(str(request.url), safe="")
        return RedirectResponse(url=f"/ui/login?next={authorize_url}", status_code=302)

    # For now, auto-approve (consent screen is issue #32)
    code = await svc.create_authorization_code(
        request=auth_request, user_id=session.user_id
    )

    params = {"code": code, "state": auth_request.state}
    return RedirectResponse(
        url=f"{auth_request.redirect_uri}?{urlencode(params)}", status_code=302
    )
