# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""MFA setup and management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select

from shomer.deps import Config, CurrentUser, DbSession
from shomer.models.user_mfa import UserMFA
from shomer.services.mfa_service import MFAService

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

    return JSONResponse(
        status_code=200,
        content={
            "secret": secret,
            "provisioning_uri": provisioning_uri,
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
