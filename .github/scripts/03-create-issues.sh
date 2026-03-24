#!/bin/bash
set -euo pipefail

REPO="${1:-goabonga/shomer}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ISSUES_DIR="$(dirname "$SCRIPT_DIR")/issues"

echo "=== Creating issues for $REPO ==="
echo "Reading issue files from: $ISSUES_DIR"
echo ""

create_issue() {
    local file="$1"
    local title="$2"
    local milestone="$3"
    local labels="$4"

    local filepath="$ISSUES_DIR/$file"
    if [[ ! -f "$filepath" ]]; then
        echo "ERROR: File not found: $filepath"
        return 1
    fi

    echo -n "Creating: $title ... "
    local url
    url=$(gh issue create --repo "$REPO" \
        --title "$title" \
        --body-file "$filepath" \
        --milestone "$milestone" \
        --label "$labels")
    echo "$url"
    sleep 0.5
}

# ============================================================
# M0 - Foundations & Infrastructure (GH #1-10)
# ============================================================

create_issue "M00-foundations/001-security-argon2id-aes256gcm.md" \
    "feat(security): Argon2id hashing and AES-256-GCM encryption module" \
    "M0 - Foundations & Infrastructure" \
    "feature:auth,type:service,size:M"

create_issue "M00-foundations/002-config-pydantic-systemd-creds.md" \
    "feat(config): Pydantic settings with systemd-creds support" \
    "M0 - Foundations & Infrastructure" \
    "type:infra,size:M"

create_issue "M00-foundations/003-db-declarative-base-alembic.md" \
    "feat(db): async SQLAlchemy declarative base, TimestampMixin, Alembic" \
    "M0 - Foundations & Infrastructure" \
    "type:model,type:infra,size:S"

create_issue "M00-foundations/004-models-user-email-password.md" \
    "feat(models): User, UserEmail and UserPassword" \
    "M0 - Foundations & Infrastructure" \
    "feature:auth,type:model,oidc:core,size:M"

create_issue "M00-foundations/005-models-user-profile-oidc.md" \
    "feat(models): UserProfile with standard OIDC claims" \
    "M0 - Foundations & Infrastructure" \
    "oidc:core,feature:profile,type:model,size:S"

create_issue "M00-foundations/006-models-session-csrf-multitenancy.md" \
    "feat(models): Session with CSRF and multi-tenancy" \
    "M0 - Foundations & Infrastructure" \
    "feature:session,type:model,size:S"

create_issue "M00-foundations/007-models-verification-password-reset.md" \
    "feat(models): VerificationCode and PasswordResetToken" \
    "M0 - Foundations & Infrastructure" \
    "feature:auth,type:model,size:S"

create_issue "M00-foundations/008-middleware-cors-cookies.md" \
    "feat(middleware): CORS and secure cookie policy" \
    "M0 - Foundations & Infrastructure" \
    "type:infra,rfc:6749,size:S"

create_issue "M00-foundations/009-deps-injection-fastapi.md" \
    "feat(deps): FastAPI dependency injection system" \
    "M0 - Foundations & Infrastructure" \
    "type:infra,size:M"

create_issue "M00-foundations/010-email-service-celery.md" \
    "feat(email): email sending service (SMTP/Mailler) via Celery" \
    "M0 - Foundations & Infrastructure" \
    "feature:email,type:service,size:L"

# ============================================================
# M1 - RFC 7517/7518 — JSON Web Keys (GH #11-13)
# ============================================================

create_issue "M01-rfc7517-jwk/011-jwks-model-encrypted.md" \
    "feat(jwks): JWK model with encrypted private key" \
    "M1 - RFC 7517/7518 — JSON Web Keys" \
    "rfc:7517,rfc:7518,feature:jwks,type:model,size:M"

create_issue "M01-rfc7517-jwk/012-jwks-rsa-key-service.md" \
    "feat(jwks): RSA key management service (generate, rotate, revoke)" \
    "M1 - RFC 7517/7518 — JSON Web Keys" \
    "rfc:7517,rfc:7518,feature:jwks,type:service,size:L"

create_issue "M01-rfc7517-jwk/013-jwks-endpoint.md" \
    "feat(jwks): GET /.well-known/jwks.json" \
    "M1 - RFC 7517/7518 — JSON Web Keys" \
    "rfc:7517,type:route,layer:api,size:S"

# ============================================================
# M2 - RFC 7519 — JSON Web Tokens (GH #14-16)
# ============================================================

create_issue "M02-rfc7519-jwt/014-token-jwt-create-service.md" \
    "feat(token): JWT creation service (access_token, id_token)" \
    "M2 - RFC 7519 — JSON Web Tokens" \
    "rfc:7519,oidc:core,type:service,size:L"

create_issue "M02-rfc7519-jwt/015-token-jwt-validate-service.md" \
    "feat(token): JWT validation service (signature, claims, expiry)" \
    "M2 - RFC 7519 — JSON Web Tokens" \
    "rfc:7519,type:service,size:M"

create_issue "M02-rfc7519-jwt/016-models-access-refresh-token.md" \
    "feat(models): AccessToken and RefreshToken" \
    "M2 - RFC 7519 — JSON Web Tokens" \
    "rfc:6749,type:model,size:M"

# ============================================================
# M3 - User Authentication (GH #17-26)
# ============================================================

create_issue "M03-user-auth/017-auth-register.md" \
    "feat(auth): POST /auth/register" \
    "M3 - User Authentication" \
    "feature:auth,type:route,layer:api,size:L"

create_issue "M03-user-auth/018-auth-verify.md" \
    "feat(auth): POST /auth/verify + POST /auth/verify/resend" \
    "M3 - User Authentication" \
    "feature:auth,type:route,layer:api,size:M"

create_issue "M03-user-auth/019-auth-login.md" \
    "feat(auth): POST /auth/login" \
    "M3 - User Authentication" \
    "feature:auth,type:route,layer:api,size:M"

create_issue "M03-user-auth/020-session-service.md" \
    "feat(session): browser session management service" \
    "M3 - User Authentication" \
    "feature:session,type:service,size:L"

create_issue "M03-user-auth/021-session-sliding-middleware.md" \
    "feat(session): sliding session expiration middleware" \
    "M3 - User Authentication" \
    "feature:session,type:infra,size:S"

create_issue "M03-user-auth/022-auth-logout.md" \
    "feat(auth): POST /auth/logout" \
    "M3 - User Authentication" \
    "feature:auth,type:route,layer:api,size:S"

create_issue "M03-user-auth/023-auth-password-reset.md" \
    "feat(auth): POST /auth/password/reset + /reset-verify" \
    "M3 - User Authentication" \
    "feature:auth,type:route,layer:api,size:M"

create_issue "M03-user-auth/024-auth-password-change.md" \
    "feat(auth): POST /auth/password/change" \
    "M3 - User Authentication" \
    "feature:auth,type:route,layer:api,size:S"

create_issue "M03-user-auth/025-ui-auth-pages.md" \
    "feat(auth): [UI] registration, verification and login pages" \
    "M3 - User Authentication" \
    "feature:auth,layer:ui,size:L"

create_issue "M03-user-auth/026-ui-password-pages.md" \
    "feat(auth): [UI] forgot password and password change pages" \
    "M3 - User Authentication" \
    "feature:auth,layer:ui,size:M"

# ============================================================
# M4 - RFC 6749 — OAuth 2.0 Core (GH #27-37)
# ============================================================

create_issue "M04-rfc6749-oauth2/027-models-oauth2-client.md" \
    "feat(models): OAuth2Client" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,type:model,size:M"

create_issue "M04-rfc6749-oauth2/028-oauth2-client-service.md" \
    "feat(oauth2): OAuth2 client management service" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,feature:oauth2,type:service,size:L"

create_issue "M04-rfc6749-oauth2/029-models-authorization-code.md" \
    "feat(models): AuthorizationCode" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,type:model,size:S"

create_issue "M04-rfc6749-oauth2/030-oauth2-issuer-resolver.md" \
    "feat(oauth2): dynamic issuer resolver service" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "oidc:core,type:service,size:S"

create_issue "M04-rfc6749-oauth2/031-oauth2-authorize.md" \
    "feat(oauth2): GET /oauth2/authorize — request validation" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,type:route,layer:api,size:XL"

create_issue "M04-rfc6749-oauth2/032-oauth2-authorize-consent.md" \
    "feat(oauth2): POST /oauth2/authorize — consent" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,feature:oauth2,type:route,layer:api,size:M"

create_issue "M04-rfc6749-oauth2/033-oauth2-token-authcode.md" \
    "feat(oauth2): POST /oauth2/token — grant_type=authorization_code" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,type:route,layer:api,size:L"

create_issue "M04-rfc6749-oauth2/034-oauth2-token-client-creds.md" \
    "feat(oauth2): POST /oauth2/token — grant_type=client_credentials" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,type:route,layer:api,size:M"

create_issue "M04-rfc6749-oauth2/035-oauth2-token-password.md" \
    "feat(oauth2): POST /oauth2/token — grant_type=password" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,type:route,layer:api,size:M"

create_issue "M04-rfc6749-oauth2/036-ui-consent-screen.md" \
    "feat(oauth2): [UI] consent screen" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,feature:oauth2,layer:ui,size:M"

create_issue "M04-rfc6749-oauth2/037-ui-oauth2-error-pages.md" \
    "feat(oauth2): [UI] OAuth2 error pages" \
    "M4 - RFC 6749 — OAuth 2.0 Core" \
    "rfc:6749,layer:ui,size:S"

# ============================================================
# M5 - RFC 7636 — PKCE (GH #38-39)
# ============================================================

create_issue "M05-rfc7636-pkce/038-pkce-service.md" \
    "feat(pkce): PKCE service (code_challenge S256/plain)" \
    "M5 - RFC 7636 — PKCE" \
    "rfc:7636,type:service,size:S"

create_issue "M05-rfc7636-pkce/039-pkce-integration.md" \
    "feat(pkce): PKCE integration in /authorize and /token" \
    "M5 - RFC 7636 — PKCE" \
    "rfc:7636,rfc:6749,layer:api,size:M"

# ============================================================
# M6 - RFC 6749 §6 — Refresh Token (GH #40)
# ============================================================

create_issue "M06-refresh-token/040-refresh-token-rotation.md" \
    "feat(oauth2): POST /oauth2/token — grant_type=refresh_token with rotation" \
    "M6 - RFC 6749 §6 — Refresh Token" \
    "rfc:6749,type:route,layer:api,size:M"

# ============================================================
# M7 - RFC 6750 — Bearer Token Usage (GH #41-42)
# ============================================================

create_issue "M07-rfc6750-bearer/041-bearer-middleware.md" \
    "feat(auth): Bearer token extraction middleware" \
    "M7 - RFC 6750 — Bearer Token Usage" \
    "rfc:6750,type:infra,size:S"

create_issue "M07-rfc6750-bearer/042-get-current-user.md" \
    "feat(auth): get_current_user dependency (Bearer + session)" \
    "M7 - RFC 6750 — Bearer Token Usage" \
    "rfc:6750,type:infra,size:M"

# ============================================================
# M8 - OIDC Core 1.0 (GH #43-48)
# ============================================================

create_issue "M08-oidc-core/043-oidc-id-token-service.md" \
    "feat(oidc): ID Token generation service (claims, nonce)" \
    "M8 - OIDC Core 1.0" \
    "oidc:core,type:service,size:M"

create_issue "M08-oidc-core/044-oidc-id-token-integration.md" \
    "feat(oidc): ID Token integration in POST /oauth2/token (scope openid)" \
    "M8 - OIDC Core 1.0" \
    "oidc:core,rfc:6749,layer:api,size:M"

create_issue "M08-oidc-core/045-oidc-userinfo.md" \
    "feat(oidc): GET/POST /userinfo" \
    "M8 - OIDC Core 1.0" \
    "oidc:core,feature:profile,type:route,layer:api,size:M"

create_issue "M08-oidc-core/046-profile-api-me.md" \
    "feat(profile): GET /api/me" \
    "M8 - OIDC Core 1.0" \
    "feature:auth,feature:profile,type:route,layer:api,size:M"

create_issue "M08-oidc-core/047-profile-api-update.md" \
    "feat(profile): PUT /api/me/profile + multi-email management" \
    "M8 - OIDC Core 1.0" \
    "feature:profile,oidc:core,type:route,layer:api,size:M"

create_issue "M08-oidc-core/048-ui-user-settings.md" \
    "feat(profile): [UI] user settings pages" \
    "M8 - OIDC Core 1.0" \
    "feature:auth,feature:profile,layer:ui,size:L"

# ============================================================
# M9 - OIDC Discovery 1.0 (GH #49)
# ============================================================

create_issue "M09-oidc-discovery/049-openid-configuration.md" \
    "feat(oidc): GET /.well-known/openid-configuration" \
    "M9 - OIDC Discovery 1.0" \
    "oidc:discovery,type:route,layer:api,size:M"

# ============================================================
# M10 - RFC 7009 — Token Revocation (GH #50)
# ============================================================

create_issue "M10-rfc7009-revocation/050-token-revocation.md" \
    "feat(oauth2): POST /oauth2/revoke" \
    "M10 - RFC 7009 — Token Revocation" \
    "rfc:7009,type:route,layer:api,size:M"

# ============================================================
# M11 - RFC 7662 — Token Introspection (GH #51)
# ============================================================

create_issue "M11-rfc7662-introspect/051-token-introspection.md" \
    "feat(oauth2): POST /oauth2/introspect" \
    "M11 - RFC 7662 — Token Introspection" \
    "rfc:7662,type:route,layer:api,size:L"

# ============================================================
# M12 - RFC 8628 — Device Authorization (GH #52-56)
# ============================================================

create_issue "M12-rfc8628-device/052-models-device-code.md" \
    "feat(models): DeviceCode" \
    "M12 - RFC 8628 — Device Authorization" \
    "rfc:8628,type:model,size:M"

create_issue "M12-rfc8628-device/053-device-auth-service.md" \
    "feat(oauth2): Device Authorization service" \
    "M12 - RFC 8628 — Device Authorization" \
    "rfc:8628,type:service,size:L"

create_issue "M12-rfc8628-device/054-device-auth-endpoint.md" \
    "feat(oauth2): POST /oauth2/device" \
    "M12 - RFC 8628 — Device Authorization" \
    "rfc:8628,type:route,layer:api,size:M"

create_issue "M12-rfc8628-device/055-device-token-grant.md" \
    "feat(oauth2): POST /oauth2/token — grant_type=device_code" \
    "M12 - RFC 8628 — Device Authorization" \
    "rfc:8628,type:route,layer:api,size:M"

create_issue "M12-rfc8628-device/056-ui-device-verify.md" \
    "feat(oauth2): [UI] device code verification page" \
    "M12 - RFC 8628 — Device Authorization" \
    "rfc:8628,layer:ui,size:M"

# ============================================================
# M13 - RFC 9126 — PAR (GH #57-59)
# ============================================================

create_issue "M13-rfc9126-par/057-models-par-request.md" \
    "feat(models): PARRequest" \
    "M13 - RFC 9126 — PAR" \
    "rfc:9126,type:model,size:S"

create_issue "M13-rfc9126-par/058-par-endpoint.md" \
    "feat(oauth2): POST /oauth2/par" \
    "M13 - RFC 9126 — PAR" \
    "rfc:9126,type:route,layer:api,size:M"

create_issue "M13-rfc9126-par/059-par-authorize-support.md" \
    "feat(oauth2): request_uri support in GET /oauth2/authorize" \
    "M13 - RFC 9126 — PAR" \
    "rfc:9126,rfc:6749,layer:api,size:M"

# ============================================================
# M14 - RFC 9101 — JAR (GH #60-61)
# ============================================================

create_issue "M14-rfc9101-jar/060-jar-validation-service.md" \
    "feat(oauth2): JAR validation service (JWT request object)" \
    "M14 - RFC 9101 — JAR" \
    "rfc:9101,type:service,size:L"

create_issue "M14-rfc9101-jar/061-jar-authorize-support.md" \
    "feat(oauth2): support \"request\" param in GET /oauth2/authorize" \
    "M14 - RFC 9101 — JAR" \
    "rfc:9101,rfc:6749,layer:api,size:M"

# ============================================================
# M15 - RFC 8693 — Token Exchange (GH #62-63)
# ============================================================

create_issue "M15-rfc8693-exchange/062-token-exchange-service.md" \
    "feat(oauth2): token exchange validation and scope escalation service" \
    "M15 - RFC 8693 — Token Exchange" \
    "rfc:8693,type:service,size:L"

create_issue "M15-rfc8693-exchange/063-token-exchange-grant.md" \
    "feat(oauth2): POST /oauth2/token — grant_type=token-exchange" \
    "M15 - RFC 8693 — Token Exchange" \
    "rfc:8693,type:route,layer:api,size:L"

# ============================================================
# M16 - MFA (GH #64-70)
# ============================================================

create_issue "M16-mfa/064-models-mfa.md" \
    "feat(models): UserMFA, MFABackupCode, MFAEmailCode" \
    "M16 - MFA" \
    "feature:mfa,type:model,size:M"

create_issue "M16-mfa/065-mfa-service.md" \
    "feat(mfa): complete MFA service (TOTP, backup codes, email fallback)" \
    "M16 - MFA" \
    "feature:mfa,type:service,size:L"

create_issue "M16-mfa/066-mfa-api-setup.md" \
    "feat(mfa): MFA setup/management API (status, setup, enable, disable, backup-codes)" \
    "M16 - MFA" \
    "feature:mfa,type:route,layer:api,size:L"

create_issue "M16-mfa/067-mfa-api-verify.md" \
    "feat(mfa): MFA verify + email fallback API (verify, email/send, email/verify)" \
    "M16 - MFA" \
    "feature:mfa,type:route,layer:api,size:M"

create_issue "M16-mfa/068-mfa-login-challenge.md" \
    "feat(auth): two-step MFA challenge in POST /auth/login" \
    "M16 - MFA" \
    "feature:mfa,feature:auth,layer:api,size:L"

create_issue "M16-mfa/069-mfa-oauth2-password.md" \
    "feat(oauth2): MFA support in grant_type=password" \
    "M16 - MFA" \
    "feature:mfa,rfc:6749,layer:api,size:M"

create_issue "M16-mfa/070-ui-mfa-pages.md" \
    "feat(mfa): [UI] TOTP setup, MFA challenge, and email fallback pages" \
    "M16 - MFA" \
    "feature:mfa,feature:auth,layer:ui,size:L"

# ============================================================
# M17 - RBAC & PAT (GH #71-78)
# ============================================================

create_issue "M17-rbac-pat/071-models-scope-role.md" \
    "feat(models): Scope, Role, RoleScope, UserRole" \
    "M17 - RBAC & PAT" \
    "feature:rbac,type:model,size:L"

create_issue "M17-rbac-pat/072-rbac-permission-service.md" \
    "feat(rbac): permission evaluation service (wildcard, expiration)" \
    "M17 - RBAC & PAT" \
    "feature:rbac,type:service,size:M"

create_issue "M17-rbac-pat/073-rbac-middleware.md" \
    "feat(rbac): RBAC authorization middleware" \
    "M17 - RBAC & PAT" \
    "feature:rbac,type:infra,size:M"

create_issue "M17-rbac-pat/074-models-pat.md" \
    "feat(models): PersonalAccessToken (prefix shm_pat_)" \
    "M17 - RBAC & PAT" \
    "feature:pat,type:model,size:M"

create_issue "M17-rbac-pat/075-pat-service.md" \
    "feat(pat): PAT service (create, validate, revoke, track usage)" \
    "M17 - RBAC & PAT" \
    "feature:pat,type:service,size:L"

create_issue "M17-rbac-pat/076-pat-api.md" \
    "feat(pat): PAT API (POST create, GET list, DELETE revoke)" \
    "M17 - RBAC & PAT" \
    "feature:pat,type:route,layer:api,size:M"

create_issue "M17-rbac-pat/077-pat-auth-middleware.md" \
    "feat(pat): PAT authentication middleware" \
    "M17 - RBAC & PAT" \
    "feature:pat,rfc:6750,type:infra,size:M"

create_issue "M17-rbac-pat/078-ui-pat-management.md" \
    "feat(pat): [UI] PAT management page" \
    "M17 - RBAC & PAT" \
    "feature:pat,layer:ui,size:M"

# ============================================================
# M18 - Multi-tenancy & Federation (GH #79-87)
# ============================================================

create_issue "M18-multitenancy/079-models-tenant.md" \
    "feat(models): Tenant, TenantMember, TenantCustomRole" \
    "M18 - Multi-tenancy & Federation" \
    "feature:tenant,type:model,size:L"

create_issue "M18-multitenancy/080-tenant-resolver-middleware.md" \
    "feat(tenant): tenant resolution middleware (subdomain, path, custom domain)" \
    "M18 - Multi-tenancy & Federation" \
    "feature:tenant,type:infra,size:L"

create_issue "M18-multitenancy/081-tenant-custom-domains.md" \
    "feat(tenant): custom domains (CNAME, Nginx, SSL Certbot)" \
    "M18 - Multi-tenancy & Federation" \
    "feature:tenant,size:XL"

create_issue "M18-multitenancy/082-tenant-branding.md" \
    "feat(tenant): branding — TenantBranding + TenantTemplate + rendering" \
    "M18 - Multi-tenancy & Federation" \
    "feature:tenant,size:L"

create_issue "M18-multitenancy/083-tenant-trust-policy.md" \
    "feat(tenant): trust policy — TenantTrustedSource + service" \
    "M18 - Multi-tenancy & Federation" \
    "feature:trust,feature:tenant,size:M"

create_issue "M18-multitenancy/084-models-identity-provider.md" \
    "feat(models): IdentityProvider and FederatedIdentity" \
    "M18 - Multi-tenancy & Federation" \
    "feature:federation,oidc:core,type:model,size:M"

create_issue "M18-multitenancy/085-federation-providers-api.md" \
    "feat(federation): GET /federation/providers" \
    "M18 - Multi-tenancy & Federation" \
    "feature:federation,type:route,layer:api,size:S"

create_issue "M18-multitenancy/086-federation-callback.md" \
    "feat(federation): GET /federation/callback — IdP callback + JIT provisioning + linking" \
    "M18 - Multi-tenancy & Federation" \
    "feature:federation,oidc:core,type:route,layer:api,size:L"

create_issue "M18-multitenancy/087-ui-federation.md" \
    "feat(federation): [UI] provider selection and callback" \
    "M18 - Multi-tenancy & Federation" \
    "feature:federation,layer:ui,size:M"

# ============================================================
# M19 - Administration & Operations (GH #88-101)
# ============================================================

create_issue "M19-admin-ops/088-admin-users-api.md" \
    "feat(admin): CRUD users API (/admin/users)" \
    "M19 - Administration & Operations" \
    "feature:admin,type:route,layer:api,size:L"

create_issue "M19-admin-ops/089-admin-clients-api.md" \
    "feat(admin): CRUD OAuth2 clients API (/admin/clients)" \
    "M19 - Administration & Operations" \
    "feature:admin,rfc:6749,type:route,layer:api,size:L"

create_issue "M19-admin-ops/090-admin-sessions-api.md" \
    "feat(admin): sessions API (/admin/sessions)" \
    "M19 - Administration & Operations" \
    "feature:admin,type:route,layer:api,size:M"

create_issue "M19-admin-ops/091-admin-jwks-api.md" \
    "feat(admin): JWKS API (/admin/jwks)" \
    "M19 - Administration & Operations" \
    "feature:admin,rfc:7517,type:route,layer:api,size:M"

create_issue "M19-admin-ops/092-admin-roles-scopes-api.md" \
    "feat(admin): roles and scopes API (/admin/roles, /admin/scopes)" \
    "M19 - Administration & Operations" \
    "feature:admin,feature:rbac,type:route,layer:api,size:L"

create_issue "M19-admin-ops/093-admin-tenants-api.md" \
    "feat(admin): tenants API (/admin/tenants) + members, branding, IdP" \
    "M19 - Administration & Operations" \
    "feature:admin,feature:tenant,type:route,layer:api,size:XL"

create_issue "M19-admin-ops/094-admin-pats-api.md" \
    "feat(admin): PATs API (/admin/pats)" \
    "M19 - Administration & Operations" \
    "feature:admin,feature:pat,type:route,layer:api,size:S"

create_issue "M19-admin-ops/095-admin-dashboard.md" \
    "feat(admin): GET /admin/dashboard" \
    "M19 - Administration & Operations" \
    "feature:admin,type:route,layer:api,size:M"

create_issue "M19-admin-ops/096-cleanup-celery-tasks.md" \
    "feat(cleanup): Celery Beat cleanup tasks for expired data" \
    "M19 - Administration & Operations" \
    "feature:cleanup,type:infra,size:L"

create_issue "M19-admin-ops/097-tenant-dns-ssl-celery.md" \
    "feat(tenant): Celery task for DNS verification + SSL provisioning" \
    "M19 - Administration & Operations" \
    "feature:tenant,type:infra,size:L"

create_issue "M19-admin-ops/098-email-mjml-templates.md" \
    "feat(email): MJML templates (verification, reset, MFA, welcome)" \
    "M19 - Administration & Operations" \
    "feature:email,size:M"

create_issue "M19-admin-ops/099-ui-admin-dashboard.md" \
    "feat(admin): [UI] dashboard" \
    "M19 - Administration & Operations" \
    "feature:admin,layer:ui,size:M"

create_issue "M19-admin-ops/100-ui-admin-users-clients.md" \
    "feat(admin): [UI] admin users and clients pages" \
    "M19 - Administration & Operations" \
    "feature:admin,layer:ui,size:L"

create_issue "M19-admin-ops/101-ui-admin-advanced.md" \
    "feat(admin): [UI] admin sessions, JWKS, roles, scopes, PATs, tenants pages" \
    "M19 - Administration & Operations" \
    "feature:admin,layer:ui,size:XL"

echo ""
echo "=== All 101 issues created for $REPO ==="
