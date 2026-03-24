#!/bin/bash
set -euo pipefail

REPO="${1:-goabonga/shomer}"

echo "=== Creating milestones for $REPO ==="

gh api repos/$REPO/milestones -f title="M0 - Foundations & Infrastructure" \
  -f description="Crypto, config, DB, base models, middleware, email, DI. Core building blocks for the entire auth server." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M1 - RFC 7517/7518 — JSON Web Keys" \
  -f description="JWK model, RSA key service, JWKS endpoint." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M2 - RFC 7519 — JSON Web Tokens" \
  -f description="JWT create/validate services, token models." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M3 - User Authentication" \
  -f description="Register, login, sessions, password, logout. API and UI." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M4 - RFC 6749 — OAuth 2.0 Core" \
  -f description="Client, AuthCode, /authorize, /token (auth_code, client_creds, password), consent." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M5 - RFC 7636 — PKCE" \
  -f description="PKCE service + integration in /authorize and /token." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M6 - RFC 6749 §6 — Refresh Token" \
  -f description="grant_type=refresh_token with mandatory rotation." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M7 - RFC 6750 — Bearer Token Usage" \
  -f description="Bearer extraction middleware + get_current_user." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M8 - OIDC Core 1.0" \
  -f description="ID Token, /userinfo, /api/me, profile, multi-email." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M9 - OIDC Discovery 1.0" \
  -f description="GET /.well-known/openid-configuration." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M10 - RFC 7009 — Token Revocation" \
  -f description="POST /oauth2/revoke." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M11 - RFC 7662 — Token Introspection" \
  -f description="POST /oauth2/introspect." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M12 - RFC 8628 — Device Authorization" \
  -f description="DeviceCode model, /device, /token polling, verify UI." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M13 - RFC 9126 — PAR" \
  -f description="PARRequest model, POST /oauth2/par, request_uri support." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M14 - RFC 9101 — JAR" \
  -f description="JAR validation service, request param support." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M15 - RFC 8693 — Token Exchange" \
  -f description="Token exchange service + grant type." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M16 - MFA" \
  -f description="TOTP, backup codes, email fallback, login challenge." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M17 - RBAC & PAT" \
  -f description="Scope, Role, RBAC middleware, PAT model/service/API." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M18 - Multi-tenancy & Federation" \
  -f description="Tenant, middleware, domains, branding, trust, IdP, social login." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M19 - Administration & Operations" \
  -f description="Admin CRUD APIs, Celery tasks, email templates, admin UI." \
  -f state="open"

echo "=== All 20 milestones created ($REPO) ==="
