# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""MFA setup, management, and verification API endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select

from shomer.deps import Config, CurrentUser, DbSession
from shomer.models.mfa_email_code import MFAEmailCode
from shomer.models.user_mfa import UserMFA
from shomer.services.mfa_service import MFAService

#: Rate limit: max email sends per user in a 5-minute window.
EMAIL_SEND_RATE_LIMIT = 3
EMAIL_SEND_WINDOW = timedelta(minutes=5)

router = APIRouter(prefix="/mfa", tags=["mfa"])


class TOTPCodeRequest(BaseModel):
    """Request body for TOTP code verification.

    Attributes
    ----------
    code : str
        The 6-digit TOTP code.
    """

    code: str


@router.get("/status")
async def mfa_status(user: CurrentUser, db: DbSession) -> JSONResponse:
    """Return the current MFA configuration for the authenticated user.

    Parameters
    ----------
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.

    Returns
    -------
    JSONResponse
        MFA status with enabled flag and active methods.
    """
    mfa = await _get_user_mfa(db, user.user_id)
    if mfa is None:
        return JSONResponse(
            content={
                "mfa_enabled": False,
                "methods": [],
            }
        )
    return JSONResponse(
        content={
            "mfa_enabled": mfa.is_enabled,
            "methods": mfa.methods,
        }
    )


@router.post("/setup")
async def mfa_setup(user: CurrentUser, db: DbSession, config: Config) -> JSONResponse:
    """Generate a TOTP secret and return the provisioning URI.

    Creates a UserMFA record if one doesn't exist. Returns the secret
    and provisioning URI for QR code display. MFA is not enabled until
    ``/mfa/enable`` is called with a valid TOTP code.

    Parameters
    ----------
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.
    config : Config
        Application settings.

    Returns
    -------
    JSONResponse
        TOTP secret, provisioning URI, and setup status.
    """
    svc = MFAService(db, config)

    mfa = await _get_user_mfa(db, user.user_id)
    if mfa is not None and mfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled. Disable first to re-setup.",
        )

    # Generate new TOTP secret
    secret = MFAService.generate_totp_secret()
    encrypted = svc.encrypt_totp_secret(secret)

    # Get user email for provisioning URI
    from shomer.models.user_email import UserEmail

    stmt = select(UserEmail).where(
        UserEmail.user_id == user.user_id,
        UserEmail.is_primary == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    primary_email = result.scalar_one_or_none()
    email = primary_email.email if primary_email else str(user.user_id)

    provisioning_uri = MFAService.get_provisioning_uri(
        secret, email=email, issuer="Shomer"
    )

    # Create or update UserMFA record (not yet enabled)
    if mfa is None:
        mfa = UserMFA(
            user_id=user.user_id,
            totp_secret_encrypted=encrypted,
            is_enabled=False,
            methods=[],
        )
        db.add(mfa)
    else:
        mfa.totp_secret_encrypted = encrypted
    await db.flush()

    qr_code = MFAService.generate_qr_code_base64(provisioning_uri)

    return JSONResponse(
        status_code=200,
        content={
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_code": qr_code,
            "message": "Scan the QR code, then call POST /mfa/enable with a TOTP code.",
        },
    )


@router.post("/enable")
async def mfa_enable(
    body: TOTPCodeRequest, user: CurrentUser, db: DbSession, config: Config
) -> JSONResponse:
    """Enable MFA by verifying a TOTP code.

    The user must have called ``/mfa/setup`` first. Verifies the TOTP
    code against the stored secret, then enables MFA and generates
    backup codes.

    Parameters
    ----------
    body : TOTPCodeRequest
        The TOTP code to verify.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.
    config : Config
        Application settings.

    Returns
    -------
    JSONResponse
        Backup codes (shown once) and confirmation.
    """
    svc = MFAService(db, config)

    mfa = await _get_user_mfa(db, user.user_id)
    if mfa is None or not mfa.totp_secret_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Call POST /mfa/setup first.",
        )
    if mfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled.",
        )

    # Verify the TOTP code
    secret = svc.decrypt_totp_secret(mfa.totp_secret_encrypted)
    if not MFAService.verify_totp_code(secret, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code.",
        )

    # Enable MFA
    mfa.is_enabled = True
    mfa.methods = ["totp", "backup"]

    # Generate backup codes
    raw_codes = MFAService.generate_backup_codes()
    await svc.store_backup_codes(mfa.id, raw_codes)
    await db.flush()

    return JSONResponse(
        content={
            "mfa_enabled": True,
            "methods": mfa.methods,
            "backup_codes": raw_codes,
            "message": "MFA enabled. Save your backup codes securely.",
        }
    )


@router.post("/disable")
async def mfa_disable(
    body: TOTPCodeRequest, user: CurrentUser, db: DbSession, config: Config
) -> JSONResponse:
    """Disable MFA by verifying a TOTP code.

    Parameters
    ----------
    body : TOTPCodeRequest
        The TOTP code to verify.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.
    config : Config
        Application settings.

    Returns
    -------
    JSONResponse
        Confirmation that MFA is disabled.
    """
    svc = MFAService(db, config)

    mfa = await _get_user_mfa(db, user.user_id)
    if mfa is None or not mfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled.",
        )

    # Verify the TOTP code
    secret = svc.decrypt_totp_secret(mfa.totp_secret_encrypted or "")
    if not MFAService.verify_totp_code(secret, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code.",
        )

    mfa.is_enabled = False
    mfa.methods = []
    mfa.totp_secret_encrypted = None
    await db.flush()

    return JSONResponse(
        content={
            "mfa_enabled": False,
            "message": "MFA has been disabled.",
        }
    )


@router.post("/backup-codes")
async def mfa_regenerate_backup_codes(
    body: TOTPCodeRequest, user: CurrentUser, db: DbSession, config: Config
) -> JSONResponse:
    """Regenerate backup codes (requires TOTP verification).

    Invalidates all existing backup codes and generates a new set.

    Parameters
    ----------
    body : TOTPCodeRequest
        The TOTP code to verify.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.
    config : Config
        Application settings.

    Returns
    -------
    JSONResponse
        New backup codes (shown once).
    """
    svc = MFAService(db, config)

    mfa = await _get_user_mfa(db, user.user_id)
    if mfa is None or not mfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled.",
        )

    # Verify the TOTP code
    secret = svc.decrypt_totp_secret(mfa.totp_secret_encrypted or "")
    if not MFAService.verify_totp_code(secret, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code.",
        )

    # Delete existing backup codes
    from shomer.models.mfa_backup_code import MFABackupCode

    stmt = select(MFABackupCode).where(MFABackupCode.user_mfa_id == mfa.id)
    result = await db.execute(stmt)
    for old_code in result.scalars().all():
        await db.delete(old_code)

    # Generate new backup codes
    raw_codes = MFAService.generate_backup_codes()
    await svc.store_backup_codes(mfa.id, raw_codes)
    await db.flush()

    return JSONResponse(
        content={
            "backup_codes": raw_codes,
            "message": "Backup codes regenerated. Save them securely.",
        }
    )


class MFAVerifyRequest(BaseModel):
    """Request body for MFA verification during login challenge.

    Attributes
    ----------
    code : str
        TOTP code or backup code.
    method : str
        Verification method: ``totp`` or ``backup``.
    """

    code: str
    method: str = "totp"


class MFAChallengeRequest(BaseModel):
    """Request body for the two-step MFA login challenge.

    Attributes
    ----------
    mfa_token : str
        Short-lived JWT from the login response.
    code : str
        TOTP code or backup code.
    method : str
        Verification method: ``totp`` or ``backup``.
    """

    mfa_token: str
    code: str
    method: str = "totp"


@router.post("/verify-challenge")
async def mfa_verify_challenge(
    body: MFAChallengeRequest, request: Request, db: DbSession, config: Config
) -> JSONResponse:
    """Complete the two-step MFA login challenge.

    Verifies the mfa_token (from login) and the MFA code, then creates
    a session and returns session cookies.

    Parameters
    ----------
    body : MFAChallengeRequest
        MFA token, code, and method.
    request : Request
        FastAPI request (for client metadata and cookies).
    db : DbSession
        Database session.
    config : Config
        Application settings.

    Returns
    -------
    JSONResponse
        Login confirmation with session cookie.
    """
    from shomer.routes.auth import verify_mfa_token

    user_id_str = verify_mfa_token(body.mfa_token, config)
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token.",
        )

    import uuid

    user_id = uuid.UUID(user_id_str)

    # Look up user MFA
    mfa = await _get_user_mfa(db, user_id)
    if mfa is None or not mfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this user.",
        )

    svc = MFAService(db, config)

    # Verify the code
    if body.method == "backup":
        valid = await svc.verify_backup_code(mfa.id, body.code)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid backup code.",
            )
    else:
        secret = svc.decrypt_totp_secret(mfa.totp_secret_encrypted or "")
        if not MFAService.verify_totp_code(secret, body.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code.",
            )

    # MFA verified — create session
    from shomer.middleware.cookies import get_cookie_policy
    from shomer.services.session_service import SessionService

    session_svc = SessionService(db)
    session, raw_token = await session_svc.create(
        user_id=user_id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    await db.flush()

    policy = get_cookie_policy(config)
    response = JSONResponse(
        content={
            "message": "MFA verification successful. Login complete.",
            "user_id": user_id_str,
        },
    )
    response.set_cookie(
        key="session_id",
        value=raw_token,
        httponly=policy.httponly,
        secure=policy.secure,
        samesite=policy.samesite,
        domain=policy.domain or None,
        max_age=86400,
    )
    response.set_cookie(
        key="csrf_token",
        value=session.csrf_token,
        httponly=False,
        secure=policy.secure,
        samesite=policy.samesite,
        domain=policy.domain or None,
        max_age=86400,
    )
    return response


class EmailCodeRequest(BaseModel):
    """Request body for email code verification.

    Attributes
    ----------
    code : str
        The 6-digit email verification code.
    """

    code: str


@router.post("/verify")
async def mfa_verify(
    body: MFAVerifyRequest, user: CurrentUser, db: DbSession, config: Config
) -> JSONResponse:
    """Verify an MFA code (TOTP or backup) during login challenge.

    Parameters
    ----------
    body : MFAVerifyRequest
        The code and verification method.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.
    config : Config
        Application settings.

    Returns
    -------
    JSONResponse
        Verification result.
    """
    svc = MFAService(db, config)

    mfa = await _get_user_mfa(db, user.user_id)
    if mfa is None or not mfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this user.",
        )

    if body.method == "backup":
        valid = await svc.verify_backup_code(mfa.id, body.code)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid backup code.",
            )
        return JSONResponse(content={"verified": True, "method": "backup"})

    # Default: TOTP verification
    secret = svc.decrypt_totp_secret(mfa.totp_secret_encrypted or "")
    if not MFAService.verify_totp_code(secret, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code.",
        )
    return JSONResponse(content={"verified": True, "method": "totp"})


@router.post("/email/send")
async def mfa_email_send(
    user: CurrentUser, db: DbSession, config: Config
) -> JSONResponse:
    """Send a 6-digit MFA code to the user's primary email.

    Rate-limited to prevent abuse.

    Parameters
    ----------
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.
    config : Config
        Application settings.

    Returns
    -------
    JSONResponse
        Confirmation that the code was sent.
    """
    mfa = await _get_user_mfa(db, user.user_id)
    if mfa is None or not mfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this user.",
        )

    # Rate limiting: check recent sends
    cutoff = datetime.now(timezone.utc) - EMAIL_SEND_WINDOW
    stmt = (
        select(func.count())
        .select_from(MFAEmailCode)
        .where(
            MFAEmailCode.user_id == user.user_id,
            MFAEmailCode.created_at >= cutoff,
        )
    )
    result = await db.execute(stmt)
    recent_count = result.scalar() or 0
    if recent_count >= EMAIL_SEND_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many email code requests. Try again later.",
        )

    # Get primary email
    from shomer.models.user_email import UserEmail

    email_stmt = select(UserEmail).where(
        UserEmail.user_id == user.user_id,
        UserEmail.is_primary == True,  # noqa: E712
    )
    email_result = await db.execute(email_stmt)
    primary_email = email_result.scalar_one_or_none()
    if primary_email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No primary email found.",
        )

    svc = MFAService(db, config)
    await svc.send_email_code(user_id=user.user_id, email=primary_email.email)

    return JSONResponse(
        content={
            "sent": True,
            "message": "Verification code sent to your email.",
        }
    )


@router.post("/email/verify")
async def mfa_email_verify(
    body: EmailCodeRequest, user: CurrentUser, db: DbSession, config: Config
) -> JSONResponse:
    """Verify an email MFA code.

    Parameters
    ----------
    body : EmailCodeRequest
        The 6-digit code.
    user : CurrentUser
        The authenticated user.
    db : DbSession
        Database session.
    config : Config
        Application settings.

    Returns
    -------
    JSONResponse
        Verification result.
    """
    mfa = await _get_user_mfa(db, user.user_id)
    if mfa is None or not mfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this user.",
        )

    svc = MFAService(db, config)
    valid = await svc.verify_email_code(user_id=user.user_id, code=body.code)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired email code.",
        )

    return JSONResponse(content={"verified": True, "method": "email"})


async def _get_user_mfa(db: object, user_id: object) -> UserMFA | None:
    """Look up the UserMFA record for a user.

    Parameters
    ----------
    db : AsyncSession
        Database session.
    user_id : uuid.UUID
        The user's ID.

    Returns
    -------
    UserMFA or None
        The MFA configuration, or None.
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    session: AsyncSession = db  # type: ignore[assignment]
    stmt = select(UserMFA).where(UserMFA.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
