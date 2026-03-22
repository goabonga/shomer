# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Database models.

All model modules are imported here so that SQLAlchemy's mapper
can resolve all relationships at configuration time.
"""

from shomer.models.access_token import AccessToken as AccessToken
from shomer.models.authorization_code import AuthorizationCode as AuthorizationCode
from shomer.models.device_code import DeviceCode as DeviceCode
from shomer.models.federated_identity import FederatedIdentity as FederatedIdentity
from shomer.models.identity_provider import IdentityProvider as IdentityProvider
from shomer.models.jwk import JWK as JWK
from shomer.models.mfa_backup_code import MFABackupCode as MFABackupCode
from shomer.models.mfa_email_code import MFAEmailCode as MFAEmailCode
from shomer.models.oauth2_client import OAuth2Client as OAuth2Client
from shomer.models.par_request import PARRequest as PARRequest
from shomer.models.password_reset_token import PasswordResetToken as PasswordResetToken
from shomer.models.personal_access_token import (
    PersonalAccessToken as PersonalAccessToken,
)
from shomer.models.refresh_token import RefreshToken as RefreshToken
from shomer.models.role import Role as Role
from shomer.models.role_scope import RoleScope as RoleScope
from shomer.models.scope import Scope as Scope
from shomer.models.session import Session as Session
from shomer.models.tenant import Tenant as Tenant
from shomer.models.tenant_branding import TenantBranding as TenantBranding
from shomer.models.tenant_custom_role import TenantCustomRole as TenantCustomRole
from shomer.models.tenant_member import TenantMember as TenantMember
from shomer.models.tenant_template import TenantTemplate as TenantTemplate
from shomer.models.tenant_trusted_source import (
    TenantTrustedSource as TenantTrustedSource,
)
from shomer.models.user import User as User
from shomer.models.user_email import UserEmail as UserEmail
from shomer.models.user_mfa import UserMFA as UserMFA
from shomer.models.user_password import UserPassword as UserPassword
from shomer.models.user_profile import UserProfile as UserProfile
from shomer.models.user_role import UserRole as UserRole
from shomer.models.verification_code import VerificationCode as VerificationCode
