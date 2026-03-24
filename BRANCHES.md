# Branch names by issue

Convention: `<prefix>/<issue-number>-<short-description>` (see [CONTRIBUTING.md](CONTRIBUTING.md#branch-naming))

## M0 — Foundations & Infrastructure

| Issue | Branch |
|-------|--------|
| #1 | `feat/1-security-argon2id-aes256gcm` |
| #2 | `feat/2-config-pydantic-systemd-creds` |
| #3 | `feat/3-db-declarative-base-alembic` |
| #4 | `feat/4-models-user-email-password` |
| #5 | `feat/5-models-user-profile-oidc` |
| #6 | `feat/6-models-session-csrf` |
| #7 | `feat/7-models-verification-password-reset` |
| #8 | `feat/8-middleware-cors-cookies` |
| #9 | `feat/9-deps-injection-fastapi` |
| #10 | `feat/10-email-service-celery` |

## M1 — RFC 7517/7518 — JSON Web Keys

| Issue | Branch |
|-------|--------|
| #11 | `feat/11-jwks-model-encrypted` |
| #12 | `feat/12-jwks-rsa-key-service` |
| #13 | `feat/13-jwks-endpoint` |

## M2 — RFC 7519 — JSON Web Tokens

| Issue | Branch |
|-------|--------|
| #14 | `feat/14-token-jwt-create-service` |
| #15 | `feat/15-token-jwt-validate-service` |
| #16 | `feat/16-models-access-refresh-token` |

## M3 — User Authentication

| Issue | Branch |
|-------|--------|
| #17 | `feat/17-auth-register` |
| #18 | `feat/18-auth-verify` |
| #19 | `feat/19-auth-login` |
| #20 | `feat/20-session-service` |
| #21 | `feat/21-session-sliding-middleware` |
| #22 | `feat/22-auth-logout` |
| #23 | `feat/23-auth-password-reset` |
| #24 | `feat/24-auth-password-change` |
| #25 | `feat/25-ui-auth-pages` |
| #26 | `feat/26-ui-password-pages` |

## M4 — RFC 6749 — OAuth 2.0 Core

| Issue | Branch |
|-------|--------|
| #27 | `feat/27-models-oauth2-client` |
| #28 | `feat/28-oauth2-client-service` |
| #29 | `feat/29-models-authorization-code` |
| #30 | `feat/30-oauth2-issuer-resolver` |
| #31 | `feat/31-oauth2-authorize` |
| #32 | `feat/32-oauth2-authorize-consent` |
| #33 | `feat/33-oauth2-token-authcode` |
| #34 | `feat/34-oauth2-token-client-creds` |
| #35 | `feat/35-oauth2-token-password` |
| #36 | `feat/36-ui-consent-screen` |
| #37 | `feat/37-ui-oauth2-error-pages` |

## M5 — RFC 7636 — PKCE

| Issue | Branch |
|-------|--------|
| #38 | `feat/38-pkce-service` |
| #39 | `feat/39-pkce-integration` |

## M6 — RFC 6749 §6 — Refresh Token

| Issue | Branch |
|-------|--------|
| #40 | `feat/40-refresh-token-rotation` |

## M7 — RFC 6750 — Bearer Token Usage

| Issue | Branch |
|-------|--------|
| #41 | `feat/41-bearer-middleware` |
| #42 | `feat/42-get-current-user` |

## M8 — OIDC Core 1.0

| Issue | Branch |
|-------|--------|
| #43 | `feat/43-oidc-id-token-service` |
| #44 | `feat/44-oidc-id-token-integration` |
| #45 | `feat/45-oidc-userinfo` |
| #46 | `feat/46-profile-api-me` |
| #47 | `feat/47-profile-api-update` |
| #48 | `feat/48-ui-user-settings` |

## M9 — OIDC Discovery 1.0

| Issue | Branch |
|-------|--------|
| #49 | `feat/49-openid-configuration` |

## M10 — RFC 7009 — Token Revocation

| Issue | Branch |
|-------|--------|
| #50 | `feat/50-token-revocation` |

## M11 — RFC 7662 — Token Introspection

| Issue | Branch |
|-------|--------|
| #51 | `feat/51-token-introspection` |

## M12 — RFC 8628 — Device Authorization

| Issue | Branch |
|-------|--------|
| #52 | `feat/52-models-device-code` |
| #53 | `feat/53-device-auth-service` |
| #54 | `feat/54-device-auth-endpoint` |
| #55 | `feat/55-device-token-grant` |
| #56 | `feat/56-ui-device-verify` |

## M13 — RFC 9126 — PAR

| Issue | Branch |
|-------|--------|
| #57 | `feat/57-models-par-request` |
| #58 | `feat/58-par-endpoint` |
| #59 | `feat/59-par-authorize-support` |

## M14 — RFC 9101 — JAR

| Issue | Branch |
|-------|--------|
| #60 | `feat/60-jar-validation-service` |
| #61 | `feat/61-jar-authorize-support` |

## M15 — RFC 8693 — Token Exchange

| Issue | Branch |
|-------|--------|
| #62 | `feat/62-token-exchange-service` |
| #63 | `feat/63-token-exchange-grant` |

## M16 — MFA

| Issue | Branch |
|-------|--------|
| #64 | `feat/64-models-mfa` |
| #65 | `feat/65-mfa-service` |
| #66 | `feat/66-mfa-api-setup` |
| #67 | `feat/67-mfa-api-verify` |
| #68 | `feat/68-mfa-login-challenge` |
| #69 | `feat/69-mfa-oauth2-password` |
| #70 | `feat/70-ui-mfa-pages` |

## M17 — RBAC & PAT

| Issue | Branch |
|-------|--------|
| #71 | `feat/71-models-scope-role` |
| #72 | `feat/72-rbac-permission-service` |
| #73 | `feat/73-rbac-middleware` |
| #74 | `feat/74-models-pat` |
| #75 | `feat/75-pat-service` |
| #76 | `feat/76-pat-api` |
| #77 | `feat/77-pat-auth-middleware` |
| #78 | `feat/78-ui-pat-management` |

## M18 — Multi-tenancy & Federation

| Issue | Branch |
|-------|--------|
| #79 | `feat/79-models-tenant` |
| #80 | `feat/80-tenant-resolver-middleware` |
| #81 | `feat/81-tenant-custom-domains` |
| #82 | `feat/82-tenant-branding` |
| #83 | `feat/83-tenant-trust-policy` |
| #84 | `feat/84-models-identity-provider` |
| #85 | `feat/85-federation-providers-api` |
| #86 | `feat/86-federation-callback` |
| #87 | `feat/87-ui-federation` |

## M19 — Administration & Operations

| Issue | Branch |
|-------|--------|
| #88 | `feat/88-admin-users-api` |
| #89 | `feat/89-admin-clients-api` |
| #90 | `feat/90-admin-sessions-api` |
| #91 | `feat/91-admin-jwks-api` |
| #92 | `feat/92-admin-roles-scopes-api` |
| #93 | `feat/93-admin-tenants-api` |
| #94 | `feat/94-admin-pats-api` |
| #95 | `feat/95-admin-dashboard` |
| #96 | `feat/96-cleanup-celery-tasks` |
| #97 | `feat/97-tenant-dns-ssl-celery` |
| #98 | `feat/98-email-mjml-templates` |
| #99 | `feat/99-ui-admin-dashboard` |
| #100 | `feat/100-ui-admin-users-clients` |
| #101 | `feat/101-ui-admin-advanced` |

## M20 — CLI Administration

| Issue | Branch |
|-------|--------|
| #102 | `feat/102-cli-framework-typer` |
| #103 | `feat/103-cli-seed` |
| #104 | `feat/104-cli-user` |
| #105 | `feat/105-cli-client` |
| #106 | `feat/106-cli-session` |
| #107 | `feat/107-cli-jwks` |
| #108 | `feat/108-cli-role-scope` |
| #109 | `feat/109-cli-tenant` |
| #110 | `feat/110-cli-pat` |
| #111 | `feat/111-cli-token` |

## M21 — Documentation

| Issue | Branch |
|-------|--------|
| #112 | `docs/112-architecture` |
| #113 | `docs/113-config-reference` |
| #114 | `docs/114-api-reference` |
| #115 | `docs/115-oauth2-flows` |
| #116 | `docs/116-oidc-integration` |
| #117 | `docs/117-mfa-guide` |
| #118 | `docs/118-multitenancy-guide` |
| #119 | `docs/119-federation-guide` |
| #120 | `docs/120-rbac-guide` |
| #121 | `docs/121-pat-guide` |
| #122 | `docs/122-deployment-hardening` |
| #123 | `docs/123-sdk-examples` |
| #124 | `docs/124-database-migrations` |
| #125 | `docs/125-troubleshooting` |

## M22 — Terraform Provider

| Issue | Branch |
|-------|--------|
| #126 | `feat/126-terraform-provider-scaffold` |
| #127 | `feat/127-terraform-resource-user` |
| #128 | `feat/128-terraform-resource-client` |
| #129 | `feat/129-terraform-resource-role-scope` |
| #130 | `feat/130-terraform-resource-tenant` |
| #131 | `feat/131-terraform-resource-idp` |
| #132 | `feat/132-terraform-resource-jwks` |
| #133 | `feat/133-terraform-datasources` |

## M23 — Kubernetes Operator

| Issue | Branch |
|-------|--------|
| #134 | `feat/134-k8s-operator-scaffold` |
| #135 | `feat/135-k8s-crd-oauth2client` |
| #136 | `feat/136-k8s-crd-user` |
| #137 | `feat/137-k8s-crd-tenant` |
| #138 | `feat/138-k8s-crd-role-scope` |
| #139 | `feat/139-k8s-crd-idp` |
| #140 | `feat/140-k8s-helm-operator` |
| #194 | `test/194-bdd-missing-happy-paths` |
| #196 | `test/196-unit-test-coverage-100` |
| #203 | `fix/203-bdd-playwright-wait` |
| #237 | `fix/237-flaky-bdd-tests` |
| #245 | `fix/245-settings-security-mfa-integration` |
| #251 | `fix/251-bdd-email-verification-retry` |
| #252 | `fix/252-bdd-login-retry` |
| #255 | `fix/255-mfa-qrcode` |
| #257 | `feat/257-ui-profile-settings-all-fields` |
| #259 | `fix/259-fix-flaky-bdd-tests` |
| #261 | `feat/261-ui-mfa-otpauth-uri` |
| #269 | `test/269-unit-test-coverage-100` |
| #274 | `feat/274-email-system-full-parity` |
| #278 | `feat/278-ui-email-management` |
| #279 | `feat/279-ui-session-management` |
| #280 | `feat/280-ui-connected-apps` |
| #281 | `feat/281-ui-org-tenant-management` |
| #282 | `feat/282-ui-avatar-upload` |
| #283 | `feat/283-ui-advanced-pat` |
| #284 | `feat/284-ui-settings-index` |
| #285 | `feat/285-api-settings-json` |
