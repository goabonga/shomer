#!/bin/bash
set -euo pipefail

REPO="${1:-goabonga/shomer}"

echo "=== Creating labels for $REPO ==="

# RFC/Spec labels (green)
gh label create "rfc:6749" --repo "$REPO" --color "0E8A16" --description "RFC 6749 - OAuth 2.0 Authorization Framework" --force
gh label create "rfc:6750" --repo "$REPO" --color "0E8A16" --description "RFC 6750 - Bearer Token Usage" --force
gh label create "rfc:7009" --repo "$REPO" --color "0E8A16" --description "RFC 7009 - Token Revocation" --force
gh label create "rfc:7517" --repo "$REPO" --color "0E8A16" --description "RFC 7517 - JSON Web Key (JWK)" --force
gh label create "rfc:7518" --repo "$REPO" --color "0E8A16" --description "RFC 7518 - JSON Web Algorithms (JWA)" --force
gh label create "rfc:7519" --repo "$REPO" --color "0E8A16" --description "RFC 7519 - JSON Web Token (JWT)" --force
gh label create "rfc:7636" --repo "$REPO" --color "0E8A16" --description "RFC 7636 - PKCE" --force
gh label create "rfc:7662" --repo "$REPO" --color "0E8A16" --description "RFC 7662 - Token Introspection" --force
gh label create "rfc:8628" --repo "$REPO" --color "0E8A16" --description "RFC 8628 - Device Authorization Grant" --force
gh label create "rfc:8693" --repo "$REPO" --color "0E8A16" --description "RFC 8693 - Token Exchange" --force
gh label create "rfc:9101" --repo "$REPO" --color "0E8A16" --description "RFC 9101 - JWT-Secured Authorization Request (JAR)" --force
gh label create "rfc:9126" --repo "$REPO" --color "0E8A16" --description "RFC 9126 - Pushed Authorization Requests (PAR)" --force

# OIDC labels (blue)
gh label create "oidc:core" --repo "$REPO" --color "1D76DB" --description "OpenID Connect Core 1.0" --force
gh label create "oidc:discovery" --repo "$REPO" --color "1D76DB" --description "OpenID Connect Discovery 1.0" --force

# Feature labels (purple)
gh label create "feature:auth" --repo "$REPO" --color "5319E7" --description "Authentication features" --force
gh label create "feature:mfa" --repo "$REPO" --color "5319E7" --description "Multi-factor authentication" --force
gh label create "feature:oauth2" --repo "$REPO" --color "5319E7" --description "OAuth2 features" --force
gh label create "feature:jwks" --repo "$REPO" --color "5319E7" --description "JWK Set management" --force
gh label create "feature:session" --repo "$REPO" --color "5319E7" --description "Session management" --force
gh label create "feature:pat" --repo "$REPO" --color "5319E7" --description "Personal Access Tokens" --force
gh label create "feature:rbac" --repo "$REPO" --color "5319E7" --description "Role-Based Access Control" --force
gh label create "feature:tenant" --repo "$REPO" --color "5319E7" --description "Multi-tenancy" --force
gh label create "feature:federation" --repo "$REPO" --color "5319E7" --description "Identity federation / Social login" --force
gh label create "feature:email" --repo "$REPO" --color "5319E7" --description "Email sending and templates" --force
gh label create "feature:admin" --repo "$REPO" --color "5319E7" --description "Administration features" --force
gh label create "feature:profile" --repo "$REPO" --color "5319E7" --description "User profile management" --force
gh label create "feature:trust" --repo "$REPO" --color "5319E7" --description "Trust policies" --force
gh label create "feature:cleanup" --repo "$REPO" --color "5319E7" --description "Data cleanup and maintenance" --force

# Type labels (yellow)
gh label create "type:model" --repo "$REPO" --color "E4E669" --description "Database model / schema" --force
gh label create "type:service" --repo "$REPO" --color "E4E669" --description "Business logic service" --force
gh label create "type:route" --repo "$REPO" --color "E4E669" --description "API route / endpoint" --force
gh label create "type:infra" --repo "$REPO" --color "E4E669" --description "Infrastructure / configuration" --force
gh label create "type:test" --repo "$REPO" --color "E4E669" --description "Tests" --force
gh label create "type:migration" --repo "$REPO" --color "E4E669" --description "Database migration" --force

# Layer labels
gh label create "layer:api" --repo "$REPO" --color "0075CA" --description "Backend API layer" --force
gh label create "layer:ui" --repo "$REPO" --color "D93F0B" --description "Frontend UI layer" --force

# Size labels
gh label create "size:S" --repo "$REPO" --color "C2E0C6" --description "Small (~0.5 day)" --force
gh label create "size:M" --repo "$REPO" --color "BFD4F2" --description "Medium (~1 day)" --force
gh label create "size:L" --repo "$REPO" --color "FEF2C0" --description "Large (~2 days)" --force
gh label create "size:XL" --repo "$REPO" --color "F9D0C4" --description "Extra Large (~3+ days)" --force

# Priority labels
gh label create "priority:critical" --repo "$REPO" --color "B60205" --description "Must be done first" --force
gh label create "priority:high" --repo "$REPO" --color "D93F0B" --description "High priority" --force
gh label create "priority:medium" --repo "$REPO" --color "FBCA04" --description "Medium priority" --force
gh label create "priority:low" --repo "$REPO" --color "0E8A16" --description "Low priority" --force

echo "=== All labels created ($REPO) ==="
