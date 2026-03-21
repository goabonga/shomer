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
    request_uri: str | None = None,
    request_object: str | None = None,
) -> Any:
    """OAuth2 authorization endpoint per RFC 6749 §4.1.1, RFC 9126, and RFC 9101.

    Validates the request, checks authentication, and either redirects
    to login, shows consent, or issues an authorization code.

    When ``request_uri`` is provided, the stored PAR parameters are
    resolved and used instead of the query parameters (RFC 9126 §4).

    When ``request`` (JWT) is provided, the JWT is validated via the
    JAR service and the parameters are merged (JWT wins on conflict).

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
    request_uri : str or None
        PAR request_uri (RFC 9126). Overrides query parameters.
    request_object : str or None
        JWT request object (RFC 9101). Mapped from ``request`` query param.

    Returns
    -------
    RedirectResponse
        Redirect to login, consent, or callback with code.
    """
    # RFC 9101: "request" query param is mapped to request_object by FastAPI
    # (since "request" collides with the FastAPI Request parameter).
    # Also check the raw query string for the "request" param.
    if request_object is None:
        raw_request_param = request.query_params.get("request")
        if raw_request_param:
            request_object = raw_request_param

    # RFC 9101 §4: validate JWT request object
    if request_object:
        if not client_id:
            return _render_oauth2_error(
                request, "invalid_request", "client_id is required with request param"
            )

        # Look up client to get JWKS
        client_svc = OAuth2ClientService(db)
        jar_client = await client_svc.get_by_client_id(client_id)
        if jar_client is None:
            return _render_oauth2_error(request, "invalid_request", "Unknown client_id")
        if not jar_client.jwks:
            return _render_oauth2_error(
                request,
                "invalid_request",
                "Client has no JWKS registered for request object verification",
            )

        from shomer.core.settings import get_settings
        from shomer.services.jar_validation_service import (
            JARError,
            JARValidationService,
        )

        jar_svc = JARValidationService(get_settings().jwt_issuer)
        try:
            jar_result = jar_svc.validate_request_object(
                request_jwt=request_object,
                client_id=client_id,
                client_jwks=jar_client.jwks,
            )
        except JARError as exc:
            return _render_oauth2_error(request, exc.error, exc.description)

        # Merge JWT params with query params (JWT wins on conflict)
        jar_params = jar_result.parameters
        client_id = jar_params.get("client_id") or client_id
        redirect_uri = jar_params.get("redirect_uri") or redirect_uri
        response_type = jar_params.get("response_type") or response_type
        scope = jar_params.get("scope") or scope
        state = jar_params.get("state") or state
        nonce = jar_params.get("nonce") or nonce
        code_challenge = jar_params.get("code_challenge") or code_challenge
        code_challenge_method = (
            jar_params.get("code_challenge_method") or code_challenge_method
        )

    # RFC 9126 §4: resolve request_uri to stored parameters
    if request_uri:
        if not client_id:
            return _render_oauth2_error(
                request, "invalid_request", "client_id is required with request_uri"
            )
        from shomer.services.par_service import PARError, PARService

        par_svc = PARService(db)
        try:
            params = await par_svc.resolve_request_uri(
                request_uri=request_uri,
                client_id=client_id,
            )
        except PARError as exc:
            return _render_oauth2_error(request, exc.error, exc.description)

        # Override query params with stored PAR parameters
        client_id = params.get("client_id") or client_id
        redirect_uri = params.get("redirect_uri") or redirect_uri
        response_type = params.get("response_type") or response_type
        scope = params.get("scope") or scope
        state = params.get("state") or state
        nonce = params.get("nonce") or nonce
        code_challenge = params.get("code_challenge") or code_challenge
        code_challenge_method = (
            params.get("code_challenge_method") or code_challenge_method
        )

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
    device_code: str = Form(""),
    refresh_token: str = Form(""),
    code_verifier: str = Form(""),
) -> JSONResponse:
    """OAuth2 token endpoint per RFC 6749 §4.1.3, §4.3, §4.4, §6 and RFC 8628.

    Supports ``authorization_code``, ``client_credentials``, ``password``,
    ``refresh_token`` and ``urn:ietf:params:oauth:grant-type:device_code`` grants.

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
        "urn:ietf:params:oauth:grant-type:device_code",
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

    if grant_type == "urn:ietf:params:oauth:grant-type:device_code":
        return await _handle_device_code_grant(
            token_svc, authenticated_client, device_code, db
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


@router.post("/introspect")
async def introspect(
    request: Request,
    db: DbSession,
    token: str = Form(...),
    token_type_hint: str = Form(""),
    client_id: str = Form(""),
    client_secret: str = Form(""),
) -> JSONResponse:
    """Introspect a token per RFC 7662.

    Returns ``active: true`` with metadata for valid tokens,
    or ``active: false`` for invalid/expired/revoked tokens.

    Parameters
    ----------
    request : Request
        Incoming request (for Authorization header).
    db : DbSession
        Database session.
    token : str
        The token to introspect.
    token_type_hint : str
        ``access_token`` or ``refresh_token`` (optional).
    client_id : str
        Client identifier.
    client_secret : str
        Client secret.

    Returns
    -------
    JSONResponse
        RFC 7662 introspection response.
    """
    # Authenticate client
    client_svc = OAuth2ClientService(db)
    auth_header = request.headers.get("authorization")
    try:
        await client_svc.authenticate_client(
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

    from shomer.services.introspection_service import IntrospectionService

    svc = IntrospectionService(db)
    result = await svc.introspect(
        token=token,
        token_type_hint=token_type_hint or None,
    )

    return JSONResponse(content=result)


@router.post("/par")
async def pushed_authorization_request(
    request: Request,
    db: DbSession,
    response_type: str = Form(""),
    redirect_uri: str = Form(""),
    scope: str = Form(""),
    state: str = Form(""),
    nonce: str = Form(""),
    code_challenge: str = Form(""),
    code_challenge_method: str = Form(""),
    client_id: str = Form(""),
    client_secret: str = Form(""),
) -> JSONResponse:
    """Pushed Authorization Request endpoint per RFC 9126 §2.

    Accepts authorization parameters via authenticated POST, validates
    them, stores the request, and returns a ``request_uri`` that the
    client can use at ``/authorize``.

    Parameters
    ----------
    request : Request
        Incoming request (for Authorization header).
    db : DbSession
        Database session.
    response_type : str
        Requested response type.
    redirect_uri : str
        Requested redirect URI.
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
    client_id : str
        Client identifier.
    client_secret : str
        Client secret.

    Returns
    -------
    JSONResponse
        RFC 9126 §2.2 response with ``request_uri`` and ``expires_in``.
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

    from shomer.services.par_service import PARError, PARService

    svc = PARService(db)
    try:
        par_response = await svc.push_authorization_request(
            client_id=authenticated_client.client_id,
            redirect_uri=redirect_uri or None,
            response_type=response_type or None,
            scope=scope or None,
            state=state or None,
            nonce=nonce or None,
            code_challenge=code_challenge or None,
            code_challenge_method=code_challenge_method or None,
        )
    except PARError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.error,
                "error_description": exc.description,
            },
        )

    return JSONResponse(
        status_code=201,
        content={
            "request_uri": par_response.request_uri,
            "expires_in": par_response.expires_in,
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/device")
async def device_authorization(
    request: Request,
    db: DbSession,
    scope: str = Form(""),
    client_id: str = Form(""),
    client_secret: str = Form(""),
) -> JSONResponse:
    """Device Authorization endpoint per RFC 8628 §3.1.

    Initiates a device authorization flow by generating a device_code
    and user_code for the client to display to the user.

    Parameters
    ----------
    request : Request
        Incoming request (for Authorization header).
    db : DbSession
        Database session.
    scope : str
        Requested scopes.
    client_id : str
        Client identifier.
    client_secret : str
        Client secret.

    Returns
    -------
    JSONResponse
        RFC 8628 §3.2 device authorization response.
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

    from shomer.core.settings import get_settings
    from shomer.services.device_auth_service import DeviceAuthService

    settings = get_settings()
    verification_uri = f"{settings.jwt_issuer}/ui/device"

    svc = DeviceAuthService(db)
    resp = await svc.create_device_code(
        client_id=authenticated_client.client_id,
        scopes=scope,
        verification_uri=verification_uri,
    )

    return JSONResponse(
        content={
            "device_code": resp.device_code,
            "user_code": resp.user_code,
            "verification_uri": resp.verification_uri,
            "verification_uri_complete": resp.verification_uri_complete,
            "expires_in": resp.expires_in,
            "interval": resp.interval,
        },
        headers={"Cache-Control": "no-store"},
    )


async def _handle_device_code_grant(
    token_svc: TokenService,
    client: Any,
    device_code: str,
    db: Any,
) -> JSONResponse:
    """Handle device_code grant per RFC 8628 §3.4-3.5.

    Parameters
    ----------
    token_svc : TokenService
        Token service instance.
    client : OAuth2Client
        The authenticated client.
    device_code : str
        The device code from polling.
    db : AsyncSession
        Database session.

    Returns
    -------
    JSONResponse
        Token response, or RFC 8628 error (authorization_pending,
        slow_down, access_denied, expired_token).
    """
    if not device_code:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_request",
                "error_description": "device_code is required",
            },
        )

    from shomer.models.device_code import DeviceCodeStatus
    from shomer.services.device_auth_service import DeviceAuthError, DeviceAuthService

    svc = DeviceAuthService(db)
    try:
        dc = await svc.check_status(device_code=device_code)
    except DeviceAuthError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.error,
                "error_description": exc.description,
            },
        )

    # Check client matches
    if dc.client_id != client.client_id:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_grant",
                "error_description": "Client mismatch",
            },
        )

    if dc.status == DeviceCodeStatus.PENDING:
        return JSONResponse(
            status_code=400,
            content={
                "error": "authorization_pending",
                "error_description": "The user has not yet completed authorization",
            },
        )

    if dc.status == DeviceCodeStatus.DENIED:
        return JSONResponse(
            status_code=400,
            content={
                "error": "access_denied",
                "error_description": "The user denied the authorization request",
            },
        )

    if dc.status != DeviceCodeStatus.APPROVED:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_grant",
                "error_description": f"Unexpected device code status: {dc.status.value}",
            },
        )

    # Approved — issue tokens
    import hashlib
    import uuid
    from datetime import datetime, timedelta, timezone

    from shomer.core.settings import get_settings
    from shomer.models.access_token import AccessToken
    from shomer.models.refresh_token import RefreshToken
    from shomer.services.token_service import TokenResponse

    settings = get_settings()
    now = datetime.now(timezone.utc)
    scopes = dc.scopes.split() if dc.scopes else []
    jti = uuid.uuid4().hex

    access_token_record = AccessToken(
        jti=jti,
        user_id=dc.user_id,
        client_id=client.client_id,
        scopes=dc.scopes,
        expires_at=now + timedelta(seconds=settings.jwt_access_token_exp),
    )
    db.add(access_token_record)

    raw_refresh = uuid.uuid4().hex
    refresh_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()
    family_id = uuid.uuid4()
    refresh_record = RefreshToken(
        token_hash=refresh_hash,
        family_id=family_id,
        user_id=dc.user_id,
        client_id=client.client_id,
        scopes=dc.scopes,
        expires_at=now + timedelta(days=30),
    )
    db.add(refresh_record)

    # Mark device code as consumed (set to expired to prevent reuse)
    dc.status = DeviceCodeStatus.EXPIRED
    await db.flush()

    access_jwt = token_svc._build_access_jwt(
        sub=str(dc.user_id),
        aud=client.client_id,
        jti=jti,
        scopes=scopes,
    )

    # Build ID token if openid scope
    id_token = None
    if "openid" in scopes:
        from shomer.services.id_token_service import IDTokenService

        id_svc = IDTokenService(settings)
        id_token = id_svc.build_id_token(
            sub=str(dc.user_id),
            aud=client.client_id,
            scopes=scopes,
        )

    response = TokenResponse(
        access_token=access_jwt,
        expires_in=settings.jwt_access_token_exp,
        refresh_token=raw_refresh,
        scope=" ".join(scopes),
        id_token=id_token,
    )

    return JSONResponse(
        content=response.to_dict(),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )
