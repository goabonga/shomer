# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""OAuth2 endpoints."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from shomer.deps import DbSession
from shomer.services.authorize_service import AuthorizeError, AuthorizeService
from shomer.services.oauth2_client_service import (
    InvalidClientError,
    OAuth2ClientService,
)
from shomer.services.session_service import SessionService
from shomer.services.token_service import TokenError, TokenService

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
) -> Any:
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
        return _render_oauth2_error(request, exc.error, exc.description)

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

    # Look up client for consent screen display
    client_svc = OAuth2ClientService(db)
    client = await client_svc.get_by_client_id(auth_request.client_id)

    # Render consent page
    from shomer.app import templates

    scope_descriptions = _describe_scopes(auth_request.validated_scopes)

    response: Any = templates.TemplateResponse(
        request,
        "oauth2/consent.html",
        {
            "client_name": client.client_name if client else auth_request.client_id,
            "scopes": scope_descriptions,
            "client_id": auth_request.client_id,
            "redirect_uri": auth_request.redirect_uri,
            "response_type": auth_request.response_type,
            "scope": auth_request.scope,
            "state": auth_request.state,
            "nonce": auth_request.nonce or "",
            "code_challenge": auth_request.code_challenge or "",
            "code_challenge_method": auth_request.code_challenge_method or "",
            "csrf_token": session.csrf_token,
            "logo_uri": client.logo_uri if client else None,
            "policy_uri": client.policy_uri if client else None,
            "tos_uri": client.tos_uri if client else None,
        },
    )
    return response


#: User-friendly messages for OAuth2 error codes.
_FRIENDLY_ERROR_MESSAGES: dict[str, str] = {
    "invalid_client": (
        "The application that sent you here is not recognized. "
        "Please contact the application developer."
    ),
    "invalid_request": (
        "The authorization request is missing required parameters. "
        "Please try again from the application."
    ),
    "unauthorized_client": (
        "The application is not authorized for this operation. "
        "Please contact the application developer."
    ),
    "access_denied": ("Access to your account was denied."),
    "server_error": ("An unexpected error occurred. Please try again later."),
}


def _render_oauth2_error(
    request: Request,
    error: str,
    error_description: str,
) -> HTMLResponse:
    """Render a user-friendly OAuth2 error page.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    error : str
        OAuth2 error code (e.g. ``invalid_client``).
    error_description : str
        Human-readable error description.

    Returns
    -------
    HTMLResponse
        Rendered error page with 400 status.
    """
    from shomer.app import templates

    friendly = _FRIENDLY_ERROR_MESSAGES.get(error, error_description)
    content = templates.TemplateResponse(
        request,
        "oauth2/error.html",
        {
            "error": error,
            "error_description": error_description,
            "friendly_message": friendly,
        },
    )
    return HTMLResponse(content=content.body, status_code=400)


#: Human-readable descriptions for common OAuth2/OIDC scopes.
_SCOPE_DESCRIPTIONS: dict[str, str] = {
    "openid": "Verify your identity",
    "profile": "View your profile information (name, picture)",
    "email": "View your email address",
    "address": "View your postal address",
    "phone": "View your phone number",
    "offline_access": "Maintain access while you are not using the application",
}


def _describe_scopes(scopes: list[str]) -> list[dict[str, str]]:
    """Map scope names to human-readable descriptions.

    Parameters
    ----------
    scopes : list[str]
        Raw scope names.

    Returns
    -------
    list[dict[str, str]]
        List of dicts with ``name`` and ``description`` keys.
    """
    return [
        {
            "name": s,
            "description": _SCOPE_DESCRIPTIONS.get(s, s),
        }
        for s in scopes
    ]


@router.post("/authorize")
async def authorize_consent(
    request: Request,
    db: DbSession,
    consent: str = Form(...),
    csrf_token: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form(...),
    scope: str = Form(""),
    state: str = Form(...),
    nonce: str = Form(""),
    code_challenge: str = Form(""),
    code_challenge_method: str = Form(""),
) -> RedirectResponse:
    """Process consent form submission.

    Creates an authorization code on approval, or redirects with
    ``error=access_denied`` on denial.

    Parameters
    ----------
    request : Request
        The incoming HTTP request.
    db : DbSession
        Injected async database session.
    consent : str
        ``"approve"`` or ``"deny"``.
    csrf_token : str
        CSRF token for validation.
    client_id : str
        OAuth2 client identifier.
    redirect_uri : str
        Validated redirect URI.
    response_type : str
        Response type (``code``).
    scope : str
        Requested scopes.
    state : str
        CSRF state parameter.
    nonce : str
        OIDC nonce.
    code_challenge : str
        PKCE code challenge.
    code_challenge_method : str
        PKCE challenge method.

    Returns
    -------
    RedirectResponse
        Redirect to callback with code or error.
    """
    # Validate session
    session_token = request.cookies.get("session_id")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    session_svc = SessionService(db)
    session = await session_svc.validate(session_token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    # CSRF validation
    from shomer.core.security import constant_time_compare

    if not constant_time_compare(csrf_token, session.csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch",
        )

    # Handle denial
    if consent != "approve":
        params = {
            "error": "access_denied",
            "error_description": "The user denied the authorization request",
            "state": state,
        }
        return RedirectResponse(
            url=f"{redirect_uri}?{urlencode(params)}", status_code=302
        )

    # Re-validate the request to ensure params haven't been tampered
    svc = AuthorizeService(db)
    try:
        auth_request = await svc.validate_request(
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope,
            state=state,
            nonce=nonce or None,
            code_challenge=code_challenge or None,
            code_challenge_method=code_challenge_method or None,
        )
    except AuthorizeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.error, "error_description": exc.description},
        )

    # Create authorization code
    code = await svc.create_authorization_code(
        request=auth_request, user_id=session.user_id
    )

    params = {"code": code, "state": auth_request.state}
    return RedirectResponse(
        url=f"{auth_request.redirect_uri}?{urlencode(params)}", status_code=302
    )


@router.post("/token")
async def token(
    request: Request,
    db: DbSession,
    grant_type: str = Form(...),
    code: str = Form(""),
    redirect_uri: str = Form(""),
    scope: str = Form(""),
    username: str = Form(""),
    password: str = Form(""),
    client_id: str = Form(""),
    client_secret: str = Form(""),
    refresh_token: str = Form(""),
    code_verifier: str = Form(""),
) -> JSONResponse:
    """OAuth2 token endpoint per RFC 6749 §4.1.3, §4.3, §4.4 and §6.

    Supports ``authorization_code``, ``client_credentials``, ``password``
    and ``refresh_token`` grants.

    Parameters
    ----------
    request : Request
        Incoming request (for Authorization header).
    db : DbSession
        Injected async database session.
    grant_type : str
        ``authorization_code``, ``client_credentials``, ``password``
        or ``refresh_token``.
    code : str
        The authorization code (authorization_code grant only).
    redirect_uri : str
        Must match the original redirect_uri (authorization_code grant only).
    scope : str
        Requested scopes (client_credentials and password grants).
    username : str
        Resource owner email (password grant).
    password : str
        Resource owner password (password grant).
    client_id : str
        Client identifier (from POST body or Basic auth).
    client_secret : str
        Client secret (from POST body or Basic auth).
    refresh_token : str
        The refresh token (refresh_token grant only).
    code_verifier : str
        PKCE code verifier (authorization_code grant only).

    Returns
    -------
    JSONResponse
        Token response per RFC 6749 §5.1 or error per §5.2.
    """
    supported_grants = {
        "authorization_code",
        "client_credentials",
        "password",
        "refresh_token",
    }
    if grant_type not in supported_grants:
        return JSONResponse(
            status_code=400,
            content={
                "error": "unsupported_grant_type",
                "error_description": f"Unsupported grant_type: {grant_type}",
            },
        )

    # Authenticate client
    client_svc = OAuth2ClientService(db)
    auth_header = request.headers.get("authorization")
    try:
        authenticated_client = await client_svc.authenticate_client(
            authorization_header=auth_header,
            body_client_id=client_id or None,
            body_client_secret=client_secret or None,
        )
    except InvalidClientError as exc:
        return JSONResponse(
            status_code=401,
            content={
                "error": "invalid_client",
                "error_description": str(exc),
            },
            headers={"WWW-Authenticate": "Basic"},
        )

    from shomer.core.settings import get_settings

    settings = get_settings()
    token_svc = TokenService(db, settings)

    if grant_type == "client_credentials":
        return await _handle_client_credentials(token_svc, authenticated_client, scope)

    if grant_type == "password":
        return await _handle_password_grant(
            token_svc, authenticated_client, username, password, scope
        )

    if grant_type == "refresh_token":
        return await _handle_refresh_token(
            token_svc, authenticated_client, refresh_token
        )

    # authorization_code grant
    try:
        response = await token_svc.exchange_authorization_code(
            code=code,
            client_id=authenticated_client.client_id,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier or None,
        )
    except TokenError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.error,
                "error_description": exc.description,
            },
        )

    return JSONResponse(
        content=response.to_dict(),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


async def _handle_client_credentials(
    token_svc: TokenService,
    client: Any,
    scope: str,
) -> JSONResponse:
    """Handle client_credentials grant per RFC 6749 §4.4.

    Parameters
    ----------
    token_svc : TokenService
        Token service instance.
    client : OAuth2Client
        The authenticated client.
    scope : str
        Requested scopes (space-separated).

    Returns
    -------
    JSONResponse
        Token response or error.
    """
    from shomer.models.oauth2_client import ClientType

    # Only confidential clients may use client_credentials
    if client.client_type != ClientType.CONFIDENTIAL:
        return JSONResponse(
            status_code=400,
            content={
                "error": "unauthorized_client",
                "error_description": (
                    "Public clients cannot use client_credentials grant"
                ),
            },
        )

    # Check grant_type is allowed for this client
    if "client_credentials" not in (client.grant_types or []):
        return JSONResponse(
            status_code=400,
            content={
                "error": "unauthorized_client",
                "error_description": (
                    "Client is not authorized for client_credentials grant"
                ),
            },
        )

    try:
        response = await token_svc.issue_client_credentials(
            client_id=client.client_id,
            client_scopes=client.scopes or [],
            requested_scope=scope or None,
        )
    except TokenError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.error,
                "error_description": exc.description,
            },
        )

    return JSONResponse(
        content=response.to_dict(),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


async def _handle_password_grant(
    token_svc: TokenService,
    client: Any,
    username: str,
    password: str,
    scope: str,
) -> JSONResponse:
    """Handle resource owner password credentials grant per RFC 6749 §4.3.

    Parameters
    ----------
    token_svc : TokenService
        Token service instance.
    client : OAuth2Client
        The authenticated client.
    username : str
        Resource owner email.
    password : str
        Resource owner password.
    scope : str
        Requested scopes (space-separated).

    Returns
    -------
    JSONResponse
        Token response or error.
    """
    # Check grant_type is allowed for this client
    if "password" not in (client.grant_types or []):
        return JSONResponse(
            status_code=400,
            content={
                "error": "unauthorized_client",
                "error_description": ("Client is not authorized for password grant"),
            },
        )

    if not username or not password:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_request",
                "error_description": "username and password are required",
            },
        )

    try:
        response = await token_svc.issue_password_grant(
            username=username,
            password=password,
            client_id=client.client_id,
            scope=scope or None,
        )
    except TokenError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.error,
                "error_description": exc.description,
            },
        )

    return JSONResponse(
        content=response.to_dict(),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


async def _handle_refresh_token(
    token_svc: TokenService,
    client: Any,
    refresh_token: str,
) -> JSONResponse:
    """Handle refresh_token grant per RFC 6749 §6.

    Parameters
    ----------
    token_svc : TokenService
        Token service instance.
    client : OAuth2Client
        The authenticated client.
    refresh_token : str
        The refresh token value.

    Returns
    -------
    JSONResponse
        Token response or error.
    """
    if not refresh_token:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_request",
                "error_description": "refresh_token is required",
            },
        )

    # Check grant_type is allowed for this client
    if "refresh_token" not in (client.grant_types or []):
        return JSONResponse(
            status_code=400,
            content={
                "error": "unauthorized_client",
                "error_description": (
                    "Client is not authorized for refresh_token grant"
                ),
            },
        )

    try:
        response = await token_svc.rotate_refresh_token(
            refresh_token=refresh_token,
            client_id=client.client_id,
        )
    except TokenError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.error,
                "error_description": exc.description,
            },
        )

    return JSONResponse(
        content=response.to_dict(),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@router.post("/revoke")
async def revoke(
    request: Request,
    db: DbSession,
    token: str = Form(...),
    token_type_hint: str = Form(""),
    client_id: str = Form(""),
    client_secret: str = Form(""),
) -> JSONResponse:
    """Revoke a token per RFC 7009.

    Always returns 200 OK, even if the token is unknown or already
    revoked (no information leakage).

    Parameters
    ----------
    request : Request
        Incoming request (for Authorization header).
    db : DbSession
        Database session.
    token : str
        The token to revoke.
    token_type_hint : str
        ``access_token`` or ``refresh_token`` (optional).
    client_id : str
        Client identifier.
    client_secret : str
        Client secret.

    Returns
    -------
    JSONResponse
        Always 200 OK.
    """
    # Authenticate client
    client_svc = OAuth2ClientService(db)
    auth_header = request.headers.get("authorization")
    try:
        authenticated_client = await client_svc.authenticate_client(
            authorization_header=auth_header,
            body_client_id=client_id or None,
            body_client_secret=client_secret or None,
        )
    except InvalidClientError as exc:
        return JSONResponse(
            status_code=401,
            content={
                "error": "invalid_client",
                "error_description": str(exc),
            },
            headers={"WWW-Authenticate": "Basic"},
        )

    from shomer.services.revocation_service import RevocationService

    svc = RevocationService(db)
    await svc.revoke(
        token=token,
        token_type_hint=token_type_hint or None,
        client_id=authenticated_client.client_id,
    )

    # RFC 7009 §2.1: always return 200
    return JSONResponse(content={}, status_code=200)
