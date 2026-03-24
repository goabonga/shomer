# Plan : Création d'issues GitHub pour le projet Shomer

## Contexte

**Pourquoi :** Réécriture du serveur OIDC/OAuth2 `auth` (Python/FastAPI, ~35K lignes, 37+ tables, 54 migrations, 100+ routes) dans un nouveau projet `shomer` (scaffolding vide avec CI/CD, Docker, Helm prêts). Les issues seront organisées par conformité RFC/spec OIDC, pas par module de code.

**Projet source :** `goabonga/auth` - serveur complet implémentant RFC 6749, 7009, 7517, 7519, 7636, 7662, 8628, 8693, 9101, 9126, OIDC Core 1.0, OIDC Discovery 1.0

**Projet cible :** `goabonga/shomer` - scaffolding vide (health checks, docs, Celery worker configuré, aucun modèle/route auth)

**Séparation API/UI :** Chaque feature qui a des composants visuels est découpée en issues jumelles (API + UI) dans le même milestone. L'issue UI dépend toujours de l'issue API correspondante. L'admin panel reste intégré dans shomer.

## Ce que va faire le plan

1. Créer les **labels** (RFC, feature, type, size, priority, layer)
2. Créer les **8 milestones**
3. Créer les **~81 issues** (63 base + 18 issues UI jumelles) avec titres, descriptions, acceptance criteria, références RFC, labels, et dépendances

---

## Phase 1 : Création des labels

```
# RFC/Spec
rfc:6749, rfc:6750, rfc:7009, rfc:7517, rfc:7518, rfc:7519, rfc:7636, rfc:7662, rfc:8628, rfc:8693, rfc:9101, rfc:9126, oidc:core, oidc:discovery

# Feature
feature:auth, feature:mfa, feature:oauth2, feature:jwks, feature:session, feature:pat, feature:rbac, feature:tenant, feature:federation, feature:email, feature:admin, feature:profile, feature:trust, feature:cleanup

# Type
type:model, type:service, type:route, type:infra, type:test, type:migration

# Layer (séparation API/UI)
layer:api, layer:ui

# Size
size:S, size:M, size:L, size:XL

# Priority
priority:critical, priority:high, priority:medium, priority:low
```

## Phase 2 : Création des milestones

| # | Milestone | Description | Issues |
|---|-----------|-------------|--------|
| M1 | Fondations & Sécurité | Infrastructure crypto, modèles de base, configuration | 8 |
| M2 | Authentification utilisateur | Inscription, login, sessions, mot de passe (API + UI) | 14 |
| M3 | JWKS & JWT | Gestion des clés, signature, vérification | 4 |
| M4 | OAuth2 Core (RFC 6749) | Authorization Code + PKCE, Client Credentials, Token endpoint (API + UI) | 10 |
| M5 | OIDC & Discovery | ID Token, UserInfo, Discovery (API + UI) | 7 |
| M6 | OAuth2 Avancé | Refresh Token, Revocation, Introspection, Device Code, PAR, JAR, Token Exchange (API + UI) | 10 |
| M7 | MFA, PAT & RBAC | Multi-facteurs, tokens personnels, contrôle d'accès (API + UI) | 10 |
| M8 | Multi-tenancy, Federation & Ops | Tenants, social login, emails, tâches planifiées, administration (API + UI) | 18 |

## Phase 3 : Création des ~81 issues

> Convention : les issues UI sont suffixées `[UI]` et portent le label `layer:ui`.
> Les issues API portent le label `layer:api` (sauf les issues infra/model qui n'ont pas de layer).

### M1 - Fondations & Sécurité (8 issues - pas de UI)

| # | Titre | Size | Deps | Labels clés |
|---|-------|------|------|-------------|
| 1 | `feat(security): module de hachage Argon2id et chiffrement AES-256-GCM` | M | - | feature:auth, type:service |
| 2 | `feat(config): configuration Pydantic avec support systemd-creds` | M | - | type:infra |
| 3 | `feat(db): declarative base, TimestampMixin et configuration Alembic` | S | - | type:model, type:infra |
| 4 | `feat(models): modèles User, UserEmail et UserPassword avec migration` | M | #3 | feature:auth, type:model, oidc:core |
| 5 | `feat(models): modèles VerificationCode et PasswordResetToken` | S | #4 | feature:auth, type:model |
| 6 | `feat(models): modèle Session avec support CSRF et multi-tenancy` | S | #4 | feature:session, type:model |
| 7 | `feat(models): modèle UserProfile avec claims OIDC standard` | S | #4 | oidc:core, feature:profile |
| 8 | `feat(middleware): configuration CORS et politique de cookies sécurisés` | S | #2 | type:infra, rfc:6749 |

### M2 - Authentification utilisateur (14 issues : 9 API + 5 UI)

| # | Titre | Size | Deps | Labels clés |
|---|-------|------|------|-------------|
| 9 | `feat(auth): API d'inscription utilisateur avec vérification par code email` | L | #1,#4,#5 | feature:auth, type:service, layer:api |
| 9b | `feat(auth): [UI] pages d'inscription et de vérification email` | M | #9 | feature:auth, type:route, layer:ui |
| 10 | `feat(auth): API de vérification d'email par code` | M | #9 | feature:auth, type:route, layer:api |
| 11 | `feat(auth): API d'authentification par email/mot de passe` | M | #1,#4 | feature:auth, rfc:6749, layer:api |
| 11b | `feat(auth): [UI] page de login avec formulaire et redirect` | M | #11 | feature:auth, type:route, layer:ui |
| 12 | `feat(session): gestion complète des sessions navigateur` | L | #1,#6 | feature:session, type:service |
| 13 | `feat(auth): endpoints de déconnexion (session unique et toutes les sessions)` | S | #12 | feature:auth, type:route, layer:api |
| 14 | `feat(auth): API de mot de passe oublié avec token de réinitialisation` | M | #1,#5,#9 | feature:auth, layer:api |
| 14b | `feat(auth): [UI] pages de demande et réinitialisation de mot de passe` | M | #14 | feature:auth, layer:ui |
| 15 | `feat(auth): API de changement de mot de passe avec vérification de l'ancien` | S | #11,#12 | feature:auth, layer:api |
| 15b | `feat(auth): [UI] page de changement de mot de passe` | S | #15 | feature:auth, layer:ui |
| 16 | `feat(deps): système d'injection de dépendances FastAPI pour les services` | M | #2,#12 | type:infra |
| 17 | `feat(email): service d'envoi d'email avec backends SMTP et Mailler via Celery` | L | #2 | feature:email, type:service |

### M3 - JWKS & JWT (4 issues - pas de UI)

| # | Titre | Size | Deps | Labels clés |
|---|-------|------|------|-------------|
| 18 | `feat(jwks): modèle JWK et service de gestion des clés RSA (RFC 7517/7518)` | L | #1,#3 | rfc:7517, rfc:7518, feature:jwks |
| 19 | `feat(jwks): endpoint /.well-known/jwks.json (RFC 7517)` | S | #18 | rfc:7517, oidc:discovery |
| 20 | `feat(token): service de création et validation des JWT (RFC 7519)` | L | #18 | rfc:7519, rfc:6749, oidc:core |
| 21 | `feat(models): modèles AccessToken et RefreshToken pour le stockage` | M | #3,#22 | rfc:6749, type:model |

### M4 - OAuth2 Core (10 issues : 8 API + 2 UI)

| # | Titre | Size | Deps | Labels clés |
|---|-------|------|------|-------------|
| 22 | `feat(models): modèle OAuth2Client avec support PKCE, PAR, JAR` | M | #3 | rfc:6749, type:model |
| 23 | `feat(oauth2): service de gestion des clients OAuth2` | L | #1,#22 | rfc:6749, feature:oauth2 |
| 24 | `feat(models): modèle AuthorizationCode avec support PKCE` | S | #22,#4 | rfc:6749, rfc:7636 |
| 25 | `feat(oauth2): service PKCE - génération et vérification code_challenge (RFC 7636)` | S | - | rfc:7636 |
| 26 | `feat(oauth2): API d'autorisation avec PKCE obligatoire (RFC 6749 + RFC 7636)` | XL | #11,#12,#23,#24,#25 | rfc:6749, rfc:7636, layer:api |
| 27 | `feat(oauth2): token endpoint pour authorization_code et client_credentials (RFC 6749)` | XL | #20,#21,#23,#25,#26 | rfc:6749, rfc:7636, oidc:core, layer:api |
| 28 | `feat(oauth2): API de traitement du consentement utilisateur` | M | #26 | rfc:6749, feature:oauth2, layer:api |
| 28b | `feat(oauth2): [UI] écran de consentement avec branding et liste des scopes` | M | #28 | rfc:6749, feature:oauth2, layer:ui |
| 26b | `feat(oauth2): [UI] pages d'erreur et de redirection d'autorisation` | S | #26 | rfc:6749, layer:ui |
| 29 | `feat(oauth2): service de résolution dynamique de l'issuer` | S | #2 | oidc:core |

### M5 - OIDC & Discovery (7 issues : 5 API + 2 UI)

| # | Titre | Size | Deps | Labels clés |
|---|-------|------|------|-------------|
| 30 | `feat(oidc): endpoint OpenID Connect Discovery` | M | #29 | oidc:discovery, layer:api |
| 31 | `feat(oidc): endpoint UserInfo avec claims standard (OIDC Core 1.0)` | M | #7,#20 | oidc:core, feature:profile, layer:api |
| 32 | `feat(profile): API de profil utilisateur et gestion multi-email` | M | #7 | oidc:core, feature:profile, layer:api |
| 33 | `feat(auth): API des paramètres utilisateur (/api/me)` | M | #12,#32 | feature:auth, feature:profile, layer:api |
| 33b | `feat(auth): [UI] pages de paramètres utilisateur (profil, sécurité, sessions)` | L | #33 | feature:auth, feature:profile, layer:ui |
| 34 | `feat(oauth2): grant type password (ROPC) avec support MFA` | M | #27,#11 | rfc:6749, feature:mfa, layer:api |

### M6 - OAuth2 Avancé (10 issues : 9 API + 1 UI)

| # | Titre | Size | Deps | Labels clés |
|---|-------|------|------|-------------|
| 35 | `feat(oauth2): refresh token grant avec rotation obligatoire` | M | #27,#21 | rfc:6749, layer:api |
| 36 | `feat(oauth2): endpoint de révocation de tokens (RFC 7009)` | M | #20,#27 | rfc:7009, layer:api |
| 37 | `feat(oauth2): endpoint d'introspection de tokens (RFC 7662)` | L | #20,#27 | rfc:7662, layer:api |
| 38 | `feat(models): modèle DeviceCode et service Device Authorization (RFC 8628)` | L | #22 | rfc:8628 |
| 39 | `feat(oauth2): API Device Authorization flow (RFC 8628)` | L | #27,#38 | rfc:8628, layer:api |
| 39b | `feat(oauth2): [UI] page de vérification device code (saisie user_code)` | M | #39 | rfc:8628, layer:ui |
| 40 | `feat(oauth2): Pushed Authorization Requests - modèle et service (RFC 9126)` | M | #22,#23 | rfc:9126 |
| 41 | `feat(oauth2): endpoint POST /oauth2/par et support request_uri dans /authorize (RFC 9126)` | M | #26,#40 | rfc:9126, layer:api |
| 42 | `feat(oauth2): JWT-Secured Authorization Requests - JAR (RFC 9101)` | L | #26,#23 | rfc:9101, layer:api |
| 43 | `feat(oauth2): grant type Token Exchange (RFC 8693)` | L | #20,#27 | rfc:8693, layer:api |

### M7 - MFA, PAT & RBAC (10 issues : 7 API + 3 UI)

| # | Titre | Size | Deps | Labels clés |
|---|-------|------|------|-------------|
| 44 | `feat(models): modèles MFA - TOTP, backup codes et codes email` | M | #4 | feature:mfa, type:model |
| 45 | `feat(mfa): service TOTP complet avec QR code, backup codes et email fallback` | L | #1,#44 | feature:mfa, type:service |
| 46 | `feat(mfa): API MFA setup/verify et login challenge 2 étapes` | L | #11,#12,#45 | feature:mfa, feature:auth, layer:api |
| 46b | `feat(mfa): [UI] pages de setup TOTP, challenge MFA et email fallback` | L | #46 | feature:mfa, feature:auth, layer:ui |
| 47 | `feat(pat): modèle et service Personal Access Tokens avec préfixe gab_pat_` | L | #1,#4 | feature:pat, type:service |
| 48 | `feat(rbac): modèles de contrôle d'accès par rôles - Scope, Role, RoleScope, UserRole` | L | #3,#4 | feature:rbac, type:model |
| 49 | `feat(rbac): middleware d'autorisation RBAC pour les routes d'administration` | M | #48,#12 | feature:rbac, type:infra |
| 63 | `feat(pat): API de gestion des Personal Access Tokens` | M | #47,#12 | feature:pat, type:route, layer:api |
| 63b | `feat(pat): [UI] page de gestion des PATs (création, liste, révocation)` | M | #63 | feature:pat, type:route, layer:ui |

### M8 - Multi-tenancy, Federation & Ops (18 issues : 13 API + 5 UI)

| # | Titre | Size | Deps | Labels clés |
|---|-------|------|------|-------------|
| 50 | `feat(tenant): modèles Tenant, TenantMember et TenantCustomRole` | L | #3,#4 | feature:tenant, type:model |
| 51 | `feat(tenant): middleware de résolution de tenant (subdomain, path, custom domain)` | L | #50 | feature:tenant, type:infra |
| 52 | `feat(tenant): domaines personnalisés avec validation CNAME, Nginx et SSL Certbot` | XL | #50,#51 | feature:tenant |
| 53 | `feat(tenant): branding par tenant - TenantBranding et TenantTemplate` | L | #50 | feature:tenant |
| 54 | `feat(tenant): politique de confiance et TenantTrustedSource` | M | #50 | feature:trust, feature:tenant |
| 55 | `feat(federation): modèles IdentityProvider et FederatedIdentity` | M | #50,#1 | feature:federation, oidc:core |
| 56 | `feat(federation): API de social login avec auto-linking et claim mapping` | L | #55,#9,#12 | feature:federation, oidc:core, layer:api |
| 56b | `feat(federation): [UI] page de sélection de provider et callback` | M | #56 | feature:federation, layer:ui |
| 57 | `feat(admin): API d'administration des utilisateurs - CRUD, activation, memberships` | L | #4,#48,#49 | feature:admin, layer:api |
| 57b | `feat(admin): [UI] pages d'administration des utilisateurs` | L | #57 | feature:admin, layer:ui |
| 58 | `feat(admin): API d'administration des clients OAuth2 - CRUD, rotation secret` | L | #22,#23,#49 | feature:admin, rfc:6749, layer:api |
| 58b | `feat(admin): [UI] pages d'administration des clients OAuth2` | L | #58 | feature:admin, layer:ui |
| 59 | `feat(admin): API d'administration sessions, JWKS, rôles/scopes, PATs et tenants` | XL | #12,#18,#48,#47,#50 | feature:admin, layer:api |
| 59b | `feat(admin): [UI] pages d'administration sessions, JWKS, rôles, PATs, tenants et dashboard` | XL | #59 | feature:admin, layer:ui |
| 60 | `feat(cleanup): tâches Celery Beat de nettoyage des données expirées` | L | #21,#24,#38,#40,#5,#6,#44,#47 | feature:cleanup |
| 61 | `feat(tenant): tâche Celery de vérification DNS et provisioning SSL` | L | #52 | feature:tenant |
| 62 | `feat(email): templates MJML pour vérification, reset, MFA et bienvenue avec branding` | M | #17,#53 | feature:email |

---

## Chemin critique (ordre d'implémentation)

```
Semaine 1-2 (M1):  #1 #2 #3 -> #4 -> #5 #6 #7 -> #8
Semaine 2-3 (M2):  #9 -> #9b #10 | #11 -> #11b | #12 -> #13 | #14 -> #14b | #15 -> #15b | #16 #17
Semaine 3-4 (M3):  #18 -> #19 | #20 -> #21
Semaine 4-5 (M4):  #22 -> #23 -> #24 | #25 | #29 -> #26 -> #26b | #27 | #28 -> #28b
Semaine 5-6 (M5):  #30 | #31 | #32 -> #33 -> #33b | #34
Semaine 6-8 (M6):  #35 #36 #37 | #38 -> #39 -> #39b | #40 -> #41 | #42 | #43
Semaine 8-10 (M7): #44 -> #45 -> #46 -> #46b | #47 -> #63 -> #63b | #48 -> #49
Semaine 10-13 (M8): #50 -> #51 -> #52 | #53 #54 | #55 -> #56 -> #56b | #57 -> #57b | #58 -> #58b | #59 -> #59b | #60 #61 #62
```

> **Principe :** Les issues API sont toujours implémentées en premier. Les issues UI peuvent être travaillées en parallèle par un autre développeur dès que l'API correspondante est terminée.

**Effort total estimé : ~100 jours-développeur** (~81 issues : 16 S + 27 M + 23 L + 7 XL + 8 issues UI supplémentaires)

---

## Exécution

Le script va :
1. Créer les labels via `gh label create` sur `goabonga/shomer`
2. Créer les 8 milestones via `gh api repos/goabonga/shomer/milestones`
3. Créer les ~81 issues via `gh issue create` avec body détaillé (description, critères d'acceptation, références RFC, dépendances)

Chaque issue body contiendra :
- Description fonctionnelle détaillée
- Critères d'acceptation (checklist)
- Références RFC avec sections spécifiques
- Dépendances (liens vers les autres issues)
- Label `layer:api` ou `layer:ui` pour la séparation
- Fichiers de référence du projet source (`auth`)


---

# Détail complet des issues (descriptions, critères d'acceptation, références RFC)

> Note : Les numéros ci-dessous correspondent à la numérotation du plan. Les issues UI jumelles (suffixe b) sont décrites dans le plan résumé ci-dessus.

## Labels a creer

```
# RFC/Spec labels
rfc:6749, rfc:6750, rfc:7009, rfc:7517, rfc:7518, rfc:7519, rfc:7636, rfc:7662,
rfc:8628, rfc:8693, rfc:9101, rfc:9126, oidc:core, oidc:discovery

# Feature labels
feature:auth, feature:mfa, feature:oauth2, feature:jwks, feature:session,
feature:pat, feature:rbac, feature:tenant, feature:federation, feature:email,
feature:admin, feature:profile, feature:trust, feature:cleanup

# Type labels
type:model, type:service, type:route, type:infra, type:test, type:migration

# Size labels
size:S, size:M, size:L, size:XL

# Priority labels
priority:critical, priority:high, priority:medium, priority:low
```

---

## M1 - Fondations & Securite

### EPIC-01: Infrastructure cryptographique et configuration

---

**Issue #1 - Module de securite : hachage Argon2id et chiffrement AES-256-GCM**

**Titre:** `feat(security): module de hachage Argon2id et chiffrement AES-256-GCM`

**Description:**
Implementer le module de securite central qui fournit :
- Hachage de mots de passe avec Argon2id (time_cost=3, memory_cost=64KB, parallelism=4)
- Verification de mot de passe et detection de besoin de rehash
- Classe `AESEncryption` pour le chiffrement AES-256-GCM (nonce 96 bits, cle 256 bits)
- Utilitaires de generation de cles et encodage base64
- Fonctions `hash_token` (SHA-256) et `generate_token` (secrets.token_hex)

**Criteres d'acceptation:**
- [ ] `hash_password(password) -> str` utilise Argon2id avec les parametres specifies
- [ ] `verify_password(password, hash) -> bool` verifie correctement
- [ ] `check_needs_rehash(hash) -> bool` detecte les anciens parametres
- [ ] `AESEncryption.encrypt(plaintext) -> bytes` produit nonce + ciphertext
- [ ] `AESEncryption.decrypt(encrypted) -> bytes` retrouve le plaintext
- [ ] `AESEncryption.from_base64(key_b64)` et `generate_key_b64()` fonctionnent
- [ ] Tests unitaires couvrent tous les cas (succes, erreur, cle invalide)

**Ref:** N/A (composant interne). Utilise par RFC 7517 (JWK encryption), RFC 6749 (token hashing).
**Labels:** `feature:auth`, `type:service`, `type:infra`, `size:M`, `priority:critical`
**Dependances:** Aucune
**Complexite:** M (1 jour)

---

**Issue #2 - Configuration applicative et gestion des secrets**

**Titre:** `feat(config): configuration Pydantic avec support systemd-creds`

**Description:**
Etendre la configuration `Settings` de shomer pour couvrir tous les parametres du serveur OIDC/OAuth2 :
- Parametres OIDC/OAuth2 (issuer, expirations tokens, codes, sessions)
- Parametres JWKS (cle de chiffrement, taille RSA, rotation)
- Parametres email (SMTP, Mailler)
- Parametres MFA, sessions, PAT
- Parametres multi-tenancy (base_domain, custom_domain)
- Fonction `get_credential()` pour lire les secrets depuis systemd credentials ou env vars

**Criteres d'acceptation:**
- [ ] Toutes les variables de configuration de l'ancienne app sont mappees
- [ ] `get_credential(name, default)` cherche dans `CREDENTIALS_DIRECTORY` puis env
- [ ] Les secrets (`jwks_encryption_key`, `smtp_password`, etc.) utilisent `get_credential`
- [ ] Valeurs par defaut coherentes (session 7j, access token 60min, refresh 30j, etc.)
- [ ] Documentation .env.example complete

**Ref:** Securite - systemd-creds pour le zero-secret-in-env en production.
**Labels:** `type:infra`, `priority:critical`, `size:M`
**Dependances:** Aucune
**Complexite:** M (1 jour)

---

**Issue #3 - Base de donnees : Base, TimestampMixin et infrastructure Alembic**

**Titre:** `feat(db): declarative base, TimestampMixin et configuration Alembic`

**Description:**
Configurer l'infrastructure SQLAlchemy pour le projet :
- `Base` declarative avec convention de nommage pour les contraintes (Alembic-friendly)
- `TimestampMixin` avec `created_at` et `updated_at` (server_default=func.now())
- Configuration Alembic avec support async (asyncpg)
- Convention de nommage : `ix_`, `uq_`, `ck_`, `fk_`, `pk_` prefixes

**Criteres d'acceptation:**
- [ ] `Base` a la naming convention configuree
- [ ] `TimestampMixin` ajoute `created_at` et `updated_at` avec timezone
- [ ] `alembic revision --autogenerate` fonctionne
- [ ] `alembic upgrade head` et `alembic downgrade` fonctionnent
- [ ] Connexion async (asyncpg) et sync (psycopg2) configurees

**Ref:** N/A (infrastructure)
**Labels:** `type:model`, `type:infra`, `priority:critical`, `size:S`
**Dependances:** Aucune
**Complexite:** S (0.5 jour)

---

**Issue #4 - Modele User, UserEmail, UserPassword**

**Titre:** `feat(models): modeles User, UserEmail et UserPassword avec migration`

**Description:**
Creer les modeles fondamentaux d'utilisateur :
- `User` : id (UUID), is_active, registration_source/client_id/tenant_id/ip/user_agent
- `UserEmail` : id, user_id (FK), email (unique), is_verified, is_primary, verified_at
- `UserPassword` : id, user_id (FK), password_hash, is_current (historique des mots de passe)
- Relations : User -> emails (1:N), User -> passwords (1:N)

**Criteres d'acceptation:**
- [ ] Les 3 tables sont creees via migration Alembic
- [ ] `users.email` supporte le multi-email avec `user_emails`
- [ ] Historique des mots de passe via `is_current` flag
- [ ] `registration_source` trace l'origine (direct, api, oauth)
- [ ] Index sur `user_emails.email` (unique), `user_emails.user_id`
- [ ] FK avec `ondelete=CASCADE`

**Ref:** OpenID Connect Core 1.0 Section 5.1 (Standard Claims - email, email_verified)
**Labels:** `type:model`, `type:migration`, `feature:auth`, `priority:critical`, `size:M`
**Dependances:** #3
**Complexite:** M (1 jour)

---

**Issue #5 - Modele VerificationCode et PasswordResetToken**

**Titre:** `feat(models): modeles VerificationCode et PasswordResetToken`

**Description:**
Tables de support pour les flux d'inscription et de reset :
- `VerificationCode` : user_id, email, code_hash (SHA-256), expires_at, used_at
- `PasswordResetToken` : user_id, email, token_hash (SHA-256), expires_at, used_at

**Criteres d'acceptation:**
- [ ] Les codes/tokens sont stockes en SHA-256, jamais en clair
- [ ] `expires_at` permet l'expiration configurable
- [ ] `used_at` empeche la reutilisation (one-time use)
- [ ] Index sur `code_hash` et `token_hash`
- [ ] Migration Alembic generee et testee

**Ref:** N/A (support pour l'inscription/reset, securite SHA-256)
**Labels:** `type:model`, `type:migration`, `feature:auth`, `priority:high`, `size:S`
**Dependances:** #4
**Complexite:** S (0.5 jour)

---

**Issue #6 - Modele Session (authentification navigateur)**

**Titre:** `feat(models): modele Session avec support CSRF et multi-tenancy`

**Description:**
Table de session pour l'authentification navigateur :
- `Session` : user_id, session_token_hash, csrf_token_hash, ip_address, user_agent, expires_at, revoked_at, tenant_id (optional FK)
- Tokens stockes en SHA-256

**Criteres d'acceptation:**
- [ ] Session token et CSRF token stockes en hash SHA-256
- [ ] `tenant_id` nullable pour le scoping tenant (NULL = session globale)
- [ ] Tracking IP + User-Agent
- [ ] `revoked_at` pour la revocation explicite
- [ ] Index sur `session_token_hash` (unique), `user_id`, `tenant_id`
- [ ] Migration Alembic

**Ref:** N/A (securite sessions). CSRF token conforme aux recommandations OWASP.
**Labels:** `type:model`, `type:migration`, `feature:session`, `priority:high`, `size:S`
**Dependances:** #4
**Complexite:** S (0.5 jour)

---

**Issue #7 - Modele UserProfile (claims OIDC)**

**Titre:** `feat(models): modele UserProfile avec claims OIDC standard`

**Description:**
Profil utilisateur stockant les claims OIDC standard :
- Identite : name, given_name, family_name, middle_name, nickname, preferred_username
- URLs : profile_url, picture_url, website
- Demographie : gender, birthdate, zoneinfo, locale
- Adresse structuree : formatted, street, locality, region, postal_code, country
- Telephone : phone_number, phone_number_verified
- Relation 1:1 avec User

**Criteres d'acceptation:**
- [ ] Tous les champs de la Section 5.1 de OIDC Core sont presents
- [ ] Adresse conforme au claim `address` (Section 5.1.1)
- [ ] Relation uselist=False avec User
- [ ] Migration Alembic

**Ref:** OpenID Connect Core 1.0 - Section 5.1 (Standard Claims), Section 5.1.1 (Address Claim)
**Labels:** `type:model`, `type:migration`, `oidc:core`, `feature:profile`, `priority:high`, `size:S`
**Dependances:** #4
**Complexite:** S (0.5 jour)

---

**Issue #8 - Middleware CORS et cookies securises**

**Titre:** `feat(middleware): configuration CORS et politique de cookies securises`

**Description:**
Configurer les middlewares de securite HTTP :
- CORS middleware avec origines configurables
- Configuration des cookies : Secure, HttpOnly, SameSite=Lax
- Headers de securite (X-Content-Type-Options, X-Frame-Options, etc.)

**Criteres d'acceptation:**
- [ ] CORS configurable par variable d'environnement
- [ ] Cookies de session Secure + HttpOnly + SameSite=Lax
- [ ] Tests verifiant les headers de securite

**Ref:** RFC 6749 Section 10.12 (Cross-Site Request Forgery)
**Labels:** `type:infra`, `feature:auth`, `priority:high`, `size:S`
**Dependances:** #2
**Complexite:** S (0.5 jour)

---

## M2 - Authentification utilisateur

### EPIC-02: Inscription, login, sessions et gestion des mots de passe

---

**Issue #9 - Service utilisateur : inscription avec verification email**

**Titre:** `feat(auth): service d'inscription utilisateur avec verification par code email`

**Description:**
Implementer le flux d'inscription complet :
- Creation User + UserEmail (is_primary=true, is_verified=false)
- Hachage mot de passe Argon2id -> UserPassword (is_current=true)
- Generation code de verification (6 chiffres, SHA-256, expiration configurable)
- Tracking source d'inscription (direct/api/oauth), IP, User-Agent
- Route POST /auth/register (formulaire + API JSON)

**Criteres d'acceptation:**
- [ ] Email normalise en lowercase
- [ ] Detection doublon email (409 Conflict)
- [ ] Code de verification genere et stocke en hash
- [ ] `registration_source` renseigne selon le contexte
- [ ] Template de page d'inscription HTML
- [ ] Tests d'integration (inscription OK, doublon, validation)

**Ref:** N/A (pre-requis pour tous les flux OAuth2/OIDC)
**Labels:** `feature:auth`, `type:service`, `type:route`, `priority:critical`, `size:L`
**Dependances:** #1, #4, #5
**Complexite:** L (2 jours)

---

**Issue #10 - Verification d'email par code**

**Titre:** `feat(auth): endpoint de verification d'email par code`

**Description:**
Endpoint de verification d'email :
- GET/POST /auth/verify avec code
- Validation code_hash, expiration, usage unique
- Marquage UserEmail.is_verified = true
- Renvoi de code si expire

**Criteres d'acceptation:**
- [ ] Code verifie contre le hash SHA-256
- [ ] Code expire rejete (configurable via `verification_code_expiry_hours`)
- [ ] Code deja utilise rejete (`used_at` non null)
- [ ] Endpoint de renvoi de code
- [ ] Page HTML de confirmation

**Ref:** N/A (verification d'identite)
**Labels:** `feature:auth`, `type:route`, `priority:high`, `size:M`
**Dependances:** #9
**Complexite:** M (1 jour)

---

**Issue #11 - Service d'authentification (login)**

**Titre:** `feat(auth): service d'authentification par email/mot de passe`

**Description:**
Service `AuthService` avec :
- `authenticate(email, password) -> User | None`
- Recherche UserEmail (verifie uniquement) -> User -> UserPassword (is_current)
- Verification Argon2id
- Verification user.is_active
- Routes GET/POST /auth/login avec redirect `?next=`

**Criteres d'acceptation:**
- [ ] Login echoue si email non verifie
- [ ] Login echoue si user inactif
- [ ] Login echoue si mot de passe incorrect
- [ ] Parametre `next` pour redirection post-login (utilise par OAuth2 authorize)
- [ ] Page HTML de login avec messages d'erreur
- [ ] Logging des tentatives (succes et echec)

**Ref:** RFC 6749 Section 3.1 (Authorization Endpoint - requires user authentication)
**Labels:** `feature:auth`, `type:service`, `type:route`, `priority:critical`, `size:M`
**Dependances:** #1, #4
**Complexite:** M (1 jour)

---

**Issue #12 - Service de session : creation, validation, revocation**

**Titre:** `feat(session): gestion complete des sessions navigateur`

**Description:**
`SessionService` implementant :
- `create_session(user_id, ip, user_agent, tenant_id?) -> (session_token, csrf_token)`
- `get_user_by_session_token(token) -> User | None` (validation + sliding window)
- `revoke_session(session_id)` et `revoke_all_sessions(user_id)`
- Cookie management : session_token dans cookie Secure/HttpOnly, csrf_token retourne separement
- Sliding window : extension automatique si >50% de la duree ecoulee

**Criteres d'acceptation:**
- [ ] Session token genere (64 chars hex), stocke en SHA-256
- [ ] CSRF token genere, stocke en SHA-256
- [ ] Sliding window etend `expires_at` automatiquement
- [ ] `get_user_by_session_token` verifie expiration et revocation
- [ ] Sessions scopees par tenant (optionnel)
- [ ] Revocation en masse par user_id
- [ ] Tests couvrant creation, validation, expiration, revocation

**Ref:** RFC 6749 Section 10.12 (CSRF protection)
**Labels:** `feature:session`, `type:service`, `priority:critical`, `size:L`
**Dependances:** #1, #6
**Complexite:** L (2 jours)

---

**Issue #13 - Endpoints de deconnexion**

**Titre:** `feat(auth): endpoints de deconnexion (session unique et toutes les sessions)`

**Description:**
- POST /auth/logout : revocation de la session courante, suppression du cookie
- POST /auth/logout/all : revocation de toutes les sessions de l'utilisateur

**Criteres d'acceptation:**
- [ ] Cookie de session supprime
- [ ] Session marquee `revoked_at` en base
- [ ] `/logout/all` revoque toutes les sessions du user
- [ ] Redirection vers /auth/login apres deconnexion

**Ref:** OpenID Connect Session Management 1.0 (optionnel)
**Labels:** `feature:auth`, `type:route`, `priority:high`, `size:S`
**Dependances:** #12
**Complexite:** S (0.5 jour)

---

**Issue #14 - Mot de passe oublie et reinitialisation**

**Titre:** `feat(auth): flux de mot de passe oublie avec token de reinitialisation`

**Description:**
Flux complet de reinitialisation :
- POST /auth/forgot-password : generation token reset (SHA-256), envoi email
- GET/POST /auth/reset-password : validation token, nouveau mot de passe
- Verification de l'historique des mots de passe (empecher reutilisation)

**Criteres d'acceptation:**
- [ ] Token de reset genere (64 chars hex), stocke en SHA-256
- [ ] Expiration configurable (`password_reset_expiry_hours`, defaut 1h)
- [ ] Token usage unique (`used_at`)
- [ ] Nouveau mot de passe != N derniers mots de passe (historique via UserPassword)
- [ ] Ancien `is_current` passe a false, nouveau cree avec `is_current=true`
- [ ] Page HTML pour le formulaire de reset

**Ref:** N/A (securite, bonnes pratiques NIST SP 800-63B)
**Labels:** `feature:auth`, `type:route`, `type:service`, `priority:high`, `size:M`
**Dependances:** #1, #5, #9
**Complexite:** M (1 jour)

---

**Issue #15 - Changement de mot de passe (authentifie)**

**Titre:** `feat(auth): changement de mot de passe avec verification de l'ancien`

**Description:**
- POST /auth/change-password (authentifie)
- Verification de l'ancien mot de passe
- Historique des mots de passe (interdiction de reutilisation)
- Mise a jour UserPassword

**Criteres d'acceptation:**
- [ ] Ancien mot de passe requis et verifie
- [ ] Nouveau != ancien et != N derniers
- [ ] UserPassword.is_current bascule correctement
- [ ] Invalidation optionnelle des autres sessions

**Ref:** N/A (securite)
**Labels:** `feature:auth`, `type:route`, `priority:medium`, `size:S`
**Dependances:** #11, #12
**Complexite:** S (0.5 jour)

---

**Issue #16 - Middleware de session et dependances d'injection**

**Titre:** `feat(deps): systeme d'injection de dependances FastAPI pour les services`

**Description:**
Creer le module `deps.py` central avec toutes les fonctions de dependance :
- `get_db()` : session async
- `get_session_service()`, `get_auth_service()`, etc.
- Extraction de l'utilisateur courant depuis le cookie de session
- Helper `get_session_cookie_name()` (scopeable par tenant)

**Criteres d'acceptation:**
- [ ] Toutes les dependances injectables via Depends()
- [ ] Lazy initialization des services
- [ ] Cookie name configurable (scoping tenant futur)

**Ref:** N/A (architecture)
**Labels:** `type:infra`, `priority:critical`, `size:M`
**Dependances:** #2, #12
**Complexite:** M (1 jour)

---

**Issue #17 - Service d'email : envoi async via Celery**

**Titre:** `feat(email): service d'envoi d'email avec backends SMTP et Mailler via Celery`

**Description:**
Infrastructure d'envoi d'email :
- Tache Celery `send_email` avec retry x3
- Backend SMTP (aiosmtplib) et backend Mailler (HTTP avec auth OAuth2)
- Templates MJML : verification email, reset password, bienvenue
- `EmailRenderer` pour le rendu des templates avec variables

**Criteres d'acceptation:**
- [ ] Tache Celery `send_email(to, subject, template, context)`
- [ ] Backend SMTP fonctionnel avec TLS
- [ ] Backend Mailler avec authentification OAuth2
- [ ] Fallback console en developpement (si SMTP non configure)
- [ ] Templates MJML rendus en HTML
- [ ] Retry automatique x3 en cas d'echec

**Ref:** N/A (infrastructure, requis pour verification email et MFA)
**Labels:** `feature:email`, `type:service`, `type:infra`, `priority:high`, `size:L`
**Dependances:** #2
**Complexite:** L (2 jours)

---

## M3 - JWKS & JWT

### EPIC-03: Gestion des cles JSON Web Key et signature JWT

---

**Issue #18 - Modele JWK et service JWKS**

**Titre:** `feat(jwks): modele JWK et service de gestion des cles RSA (RFC 7517/7518)`

**Description:**
Modele et service pour les cles de signature :
- `JWK` : kid, kty (RSA), alg (RS256), use (sig), private_key_encrypted (AES-256-GCM), public_key_pem, is_active, revoked_at
- `JWKSService` : generate_key, get_active_key, activate_key, revoke_key, rotate_keys, delete_key
- Cles privees chiffrees avec AES-256-GCM avant stockage
- Conversion vers format JWK public (n, e en base64url)

**Criteres d'acceptation:**
- [ ] Generation de paire RSA-2048 avec chiffrement de la cle privee
- [ ] Une seule cle active a la fois (deactivation des autres)
- [ ] Rotation : nouvelle cle generee et activee, ancienne conservee pour verification
- [ ] `to_jwk_public()` retourne le format JWK standard (kty, use, alg, kid, n, e)
- [ ] Cles revoquees exclues de la signature mais gardees pour verification
- [ ] `decrypt_private_key()` dechiffre et retourne RSAPrivateKey

**Ref:** RFC 7517 (JSON Web Key), RFC 7518 (JWA - RS256), RFC 7519 (JWT)
**Labels:** `rfc:7517`, `rfc:7518`, `feature:jwks`, `type:model`, `type:service`, `priority:critical`, `size:L`
**Dependances:** #1, #3
**Complexite:** L (2 jours)

---

**Issue #19 - Endpoint JWKS (/.well-known/jwks.json)**

**Titre:** `feat(jwks): endpoint /.well-known/jwks.json (RFC 7517)`

**Description:**
Endpoint public exposant les cles publiques :
- GET /.well-known/jwks.json
- Retourne toutes les cles non-revoquees au format JWK Set
- Cache-Control headers appropriate

**Criteres d'acceptation:**
- [ ] Retourne `{"keys": [...]}`  avec chaque cle en format JWK
- [ ] Inclut les cles actives et inactives (non revoquees) pour la verification
- [ ] Exclut les cles revoquees
- [ ] Chaque cle contient : kty, use, alg, kid, n, e
- [ ] Pas d'authentification requise (endpoint public)

**Ref:** RFC 7517 Section 5 (JWK Set Format), OpenID Connect Discovery 1.0 Section 3 (jwks_uri)
**Labels:** `rfc:7517`, `oidc:discovery`, `feature:jwks`, `type:route`, `priority:critical`, `size:S`
**Dependances:** #18
**Complexite:** S (0.5 jour)

---

**Issue #20 - Service Token : creation et validation JWT**

**Titre:** `feat(token): service de creation et validation des JWT (RFC 7519)`

**Description:**
`TokenService` central utilisant JWKSService :
- `create_access_token()` : JWT signe RS256 avec claims standard (iss, sub, aud, exp, iat, jti, scope, client_id)
- `validate_access_token()` : verification signature, expiration, revocation
- `create_id_token()` : JWT OIDC avec claims (iss, sub, aud, exp, iat, nonce, auth_time, at_hash)
- `hash_token()` et `generate_token()` pour les tokens opaques

**Criteres d'acceptation:**
- [ ] Access token JWT signe avec la cle active (header kid)
- [ ] Claims conformes : iss, sub, aud, exp, iat, jti, scope, client_id
- [ ] Expiration per-client ou globale (configurable)
- [ ] Validation : decode header -> get kid -> verify signature -> check revocation
- [ ] ID token avec at_hash (SHA-256 de l'access token, premiere moitie, base64url)
- [ ] Support `nonce` pour OIDC
- [ ] Support `act` claim pour Token Exchange (RFC 8693)

**Ref:** RFC 7519 (JWT), RFC 6749 Section 1.4 (Access Token), OpenID Connect Core 1.0 Section 2 (ID Token)
**Labels:** `rfc:7519`, `rfc:6749`, `oidc:core`, `feature:oauth2`, `type:service`, `priority:critical`, `size:L`
**Dependances:** #18
**Complexite:** L (2 jours)

---

**Issue #21 - Modeles AccessToken et RefreshToken**

**Titre:** `feat(models): modeles AccessToken et RefreshToken pour le stockage des tokens`

**Description:**
Tables pour le suivi des tokens emis :
- `AccessToken` : jti (unique), client_id (FK), user_id (FK nullable), scopes, expires_at, revoked_at
- `RefreshToken` : token_hash (SHA-256), access_token_id (FK), client_id (FK), user_id (FK nullable), scopes, expires_at, revoked_at, used_at

**Criteres d'acceptation:**
- [ ] `jti` pour les access tokens (identifiant en clair pour introspection)
- [ ] `token_hash` SHA-256 pour les refresh tokens (opaques)
- [ ] `used_at` sur RefreshToken pour la rotation (one-time use)
- [ ] `user_id` nullable (client_credentials n'a pas de user)
- [ ] Relations vers OAuth2Client et User
- [ ] Index sur jti, token_hash, client_id, user_id

**Ref:** RFC 6749 Section 1.4 (Access Token), Section 1.5 (Refresh Token)
**Labels:** `rfc:6749`, `type:model`, `type:migration`, `feature:oauth2`, `priority:critical`, `size:M`
**Dependances:** #3, #22 (OAuth2Client)
**Complexite:** M (1 jour)

---

## M4 - OAuth2 Core (RFC 6749)

### EPIC-04: Modele client, Authorization Code et Token Endpoint

---

**Issue #22 - Modele OAuth2Client**

**Titre:** `feat(models): modele OAuth2Client avec support PKCE, PAR, JAR`

**Description:**
Modele complet du client OAuth2 :
- client_id (unique), client_secret_hash, name, description, homepage_url
- redirect_uris (ARRAY), allowed_scopes (ARRAY), allowed_grant_types (ARRAY)
- token_endpoint_auth_method, is_confidential, is_active
- require_pkce (defaut true), require_consent (defaut true)
- JAR : jwks_uri, request_object_signing_alg
- allowed_origins (CORS), access_token_expiry_seconds, refresh_token_expiry_seconds
- tenant_id (FK nullable pour scoping tenant)

**Criteres d'acceptation:**
- [ ] `client_id` unique index, `client_secret_hash` nullable (public clients)
- [ ] `require_pkce` par defaut true (RFC 7636 best practice)
- [ ] `allowed_grant_types` supporte : authorization_code, refresh_token, client_credentials, device_code, token-exchange
- [ ] `token_endpoint_auth_method` : client_secret_basic, client_secret_post, none
- [ ] `tenant_id` nullable (NULL = client global)
- [ ] Expirations per-client overridables
- [ ] Migration Alembic

**Ref:** RFC 6749 Section 2 (Client Registration), RFC 7591 (Dynamic Client Registration optionnel)
**Labels:** `rfc:6749`, `type:model`, `type:migration`, `feature:oauth2`, `priority:critical`, `size:M`
**Dependances:** #3
**Complexite:** M (1 jour)

---

**Issue #23 - Service OAuth2Client : CRUD et validation**

**Titre:** `feat(oauth2): service de gestion des clients OAuth2`

**Description:**
`OAuth2ClientService` avec :
- CRUD : create, get_by_client_id, update, delete
- `verify_client_secret()` (Argon2id)
- `validate_redirect_uri(client, uri)` : comparaison exacte
- `validate_scopes(client, scopes)` : verification d'inclusion
- `validate_grant_type(client, grant_type)`
- `create_authorization_code()` et `consume_authorization_code()`
- Rotation de secret client

**Criteres d'acceptation:**
- [ ] Secret client hashe en Argon2id
- [ ] `validate_redirect_uri` : match exact, supporte http localhost + https + custom schemes
- [ ] `validate_scopes` : tous les scopes doivent etre dans allowed_scopes
- [ ] `create_authorization_code` : genere code, stocke hash, PKCE challenge, nonce, state
- [ ] `consume_authorization_code` : marque used_at, verifie non-expire, non-utilise
- [ ] Rotation de secret : nouveau secret genere, ancien invalide

**Ref:** RFC 6749 Section 2.3 (Client Authentication), Section 3.1.2.1 (Redirect URI validation)
**Labels:** `rfc:6749`, `feature:oauth2`, `type:service`, `priority:critical`, `size:L`
**Dependances:** #1, #22
**Complexite:** L (2 jours)

---

**Issue #24 - Modele AuthorizationCode**

**Titre:** `feat(models): modele AuthorizationCode avec support PKCE`

**Description:**
- `AuthorizationCode` : code_hash (SHA-256, unique), client_id (FK), user_id (FK), redirect_uri, scopes, code_challenge, code_challenge_method, nonce, state, expires_at, used_at

**Criteres d'acceptation:**
- [ ] `code_hash` unique index (SHA-256 du code original)
- [ ] `code_challenge` et `code_challenge_method` pour PKCE
- [ ] `nonce` pour OIDC
- [ ] `used_at` pour empecher la reutilisation
- [ ] Migration Alembic

**Ref:** RFC 6749 Section 4.1.2 (Authorization Code), RFC 7636 Section 4 (PKCE)
**Labels:** `rfc:6749`, `rfc:7636`, `type:model`, `type:migration`, `feature:oauth2`, `priority:critical`, `size:S`
**Dependances:** #22, #4
**Complexite:** S (0.5 jour)

---

**Issue #25 - Service PKCE (RFC 7636)**

**Titre:** `feat(oauth2): service PKCE - generation et verification code_challenge (RFC 7636)`

**Description:**
Module `pkce.py` :
- `is_valid_code_challenge_method(method)` : accepte S256 (et plain pour compat)
- `is_valid_code_challenge(challenge)` : validation format base64url
- `is_valid_code_verifier(verifier)` : longueur 43-128, caracteres [A-Z][a-z][0-9]-._~
- `verify_code_challenge(verifier, challenge, method)` : SHA-256(verifier) == challenge

**Criteres d'acceptation:**
- [ ] S256 : `BASE64URL(SHA256(code_verifier)) == code_challenge`
- [ ] `plain` supporte pour compatibilite mais S256 recommande
- [ ] Verification format code_verifier (RFC 7636 Section 4.1 : 43-128 chars unreserved)
- [ ] Verification format code_challenge (base64url sans padding)
- [ ] Tests exhaustifs (vecteurs de test RFC)

**Ref:** RFC 7636 Section 4.1 (code_verifier), Section 4.2 (code_challenge), Section 4.6 (Verification)
**Labels:** `rfc:7636`, `feature:oauth2`, `type:service`, `priority:critical`, `size:S`
**Dependances:** Aucune
**Complexite:** S (0.5 jour)

---

**Issue #26 - Endpoint Authorization (/oauth2/authorize) avec PKCE**

**Titre:** `feat(oauth2): endpoint d'autorisation GET/POST avec PKCE obligatoire (RFC 6749 + RFC 7636)`

**Description:**
Implementation complete de l'endpoint d'autorisation :
- GET /oauth2/authorize : validation parametres, verification session, redirection login si non authentifie, affichage consentement si requis, generation code si auto-consent
- POST /oauth2/authorize : traitement du formulaire de consentement (allow/deny)
- Validation : client_id, response_type=code, redirect_uri, scope, PKCE
- Support `prompt=login` pour forcer la re-authentification
- Redirection vers redirect_uri avec code et state

**Criteres d'acceptation:**
- [ ] Validation client_id contre la base
- [ ] Verification redirect_uri dans les URIs enregistrees du client
- [ ] PKCE obligatoire si `require_pkce=true` sur le client
- [ ] code_challenge_method default a S256
- [ ] Redirection vers /auth/login?next= si non authentifie
- [ ] Affichage page de consentement si `require_consent=true`
- [ ] Generation code et redirection avec `?code=...&state=...`
- [ ] Erreurs redirigees vers redirect_uri (sauf erreurs client_id/redirect_uri -> page erreur)
- [ ] Support `prompt=login` (force re-auth)

**Ref:** RFC 6749 Section 4.1.1 (Authorization Request), Section 4.1.2 (Authorization Response), RFC 7636 Section 4 (PKCE)
**Labels:** `rfc:6749`, `rfc:7636`, `feature:oauth2`, `type:route`, `priority:critical`, `size:XL`
**Dependances:** #11, #12, #23, #24, #25
**Complexite:** XL (3 jours)

---

**Issue #27 - Endpoint Token (/oauth2/token) : Authorization Code + Client Credentials**

**Titre:** `feat(oauth2): token endpoint pour authorization_code et client_credentials (RFC 6749)`

**Description:**
POST /oauth2/token avec support de :
- `grant_type=authorization_code` : echange code contre tokens (PKCE verification)
- `grant_type=client_credentials` : auth machine-to-machine
- Authentification client : Basic auth ou form-encoded
- Response : access_token (JWT), token_type, expires_in, refresh_token, scope, id_token (si openid)

**Criteres d'acceptation:**
- [ ] Authorization Code : verification code, redirect_uri match, PKCE verifier, emission token pair
- [ ] Client Credentials : client confidentiel requis, pas de refresh_token, pas de user_id
- [ ] Authentification client : `Authorization: Basic` et form-encoded `client_id/client_secret`
- [ ] `grant_type` valide dans les `allowed_grant_types` du client
- [ ] ID token emis si scope `openid` present (avec nonce et at_hash)
- [ ] Erreurs conformes RFC 6749 Section 5.2 (error, error_description)
- [ ] Code marque comme utilise apres echange (one-time use)

**Ref:** RFC 6749 Section 4.1.3 (Token Request), Section 4.1.4 (Token Response), Section 4.4 (Client Credentials), Section 5.2 (Error Response)
**Labels:** `rfc:6749`, `rfc:7636`, `oidc:core`, `feature:oauth2`, `type:route`, `priority:critical`, `size:XL`
**Dependances:** #20, #21, #23, #25, #26
**Complexite:** XL (3 jours)

---

**Issue #28 - Ecran de consentement utilisateur**

**Titre:** `feat(oauth2): ecran de consentement avec branding et liste des scopes`

**Description:**
Page HTML de consentement :
- Affiche le nom du client, les scopes demandes, redirect_uri
- Boutons "Autoriser" / "Refuser"
- POST vers /oauth2/authorize avec le choix
- Support du branding par tenant (futur)

**Criteres d'acceptation:**
- [ ] Template Jinja2 `oauth2/consent.html`
- [ ] Affiche les scopes en langage lisible
- [ ] Formulaire POST avec CSRF protection
- [ ] "Refuser" redirige avec `error=access_denied`
- [ ] "Autoriser" genere le code et redirige

**Ref:** RFC 6749 Section 4.1.1 (End-user authorization)
**Labels:** `rfc:6749`, `feature:oauth2`, `type:route`, `priority:high`, `size:M`
**Dependances:** #26
**Complexite:** M (1 jour)

---

**Issue #29 - Service Issuer : resolution dynamique de l'issuer par contexte tenant**

**Titre:** `feat(oauth2): service de resolution dynamique de l'issuer`

**Description:**
`get_issuer_from_context(db)` :
- Determine l'issuer URL en fonction du tenant actif
- Ne jamais deriver l'issuer du header Host (securite)
- Fallback sur `settings.issuer` ou `http://localhost:8000`

**Criteres d'acceptation:**
- [ ] Issuer derive de la configuration tenant (base_domain + slug ou custom_domain)
- [ ] Jamais derive du header Host (prevention d'attaque)
- [ ] Fallback sur settings.issuer si pas de tenant
- [ ] Utilise partout : tokens, discovery, userinfo

**Ref:** OpenID Connect Core 1.0 Section 15.1 (Issuer Identifier), RFC 6749 Section 1.1 (issuer)
**Labels:** `oidc:core`, `feature:oauth2`, `type:service`, `priority:high`, `size:S`
**Dependances:** #2
**Complexite:** S (0.5 jour)

---

## M5 - OIDC & Discovery

### EPIC-05: OpenID Connect Discovery, UserInfo et ID Token

---

**Issue #30 - Endpoint Discovery (/.well-known/openid-configuration)**

**Titre:** `feat(oidc): endpoint OpenID Connect Discovery (OpenID Connect Discovery 1.0)`

**Description:**
GET /.well-known/openid-configuration retournant :
- issuer, authorization_endpoint, token_endpoint, userinfo_endpoint, jwks_uri
- revocation_endpoint, introspection_endpoint, device_authorization_endpoint, pushed_authorization_request_endpoint
- scopes_supported, response_types_supported, grant_types_supported
- id_token_signing_alg_values_supported, token_endpoint_auth_methods_supported
- code_challenge_methods_supported, claims_supported
- request_parameter_supported, request_uri_parameter_supported

**Criteres d'acceptation:**
- [ ] Tous les endpoints listes avec l'issuer correct
- [ ] `scopes_supported` : openid, profile, email, offline_access
- [ ] `grant_types_supported` inclut device_code et token-exchange
- [ ] `code_challenge_methods_supported` : S256, plain
- [ ] `request_parameter_supported: true` (JAR)
- [ ] `request_uri_parameter_supported: true` (PAR)
- [ ] Endpoint public, pas d'authentification

**Ref:** OpenID Connect Discovery 1.0 Section 3 (OpenID Provider Configuration Response)
**Labels:** `oidc:discovery`, `type:route`, `priority:critical`, `size:M`
**Dependances:** #29
**Complexite:** M (1 jour)

---

**Issue #31 - Endpoint UserInfo (GET/POST /userinfo)**

**Titre:** `feat(oidc): endpoint UserInfo avec claims standard (OpenID Connect Core 1.0)`

**Description:**
Endpoint protege retournant les claims utilisateur :
- GET et POST /userinfo
- Authentification : Bearer token (access token JWT)
- Retourne les claims selon les scopes :
  - `openid` : sub
  - `profile` : name, given_name, family_name, etc.
  - `email` : email, email_verified
  - `address` : objet address
  - `phone` : phone_number, phone_number_verified

**Criteres d'acceptation:**
- [ ] Authentification via `Authorization: Bearer <access_token>`
- [ ] Validation du JWT (signature, expiration, revocation)
- [ ] Claims filtres selon les scopes du token
- [ ] Scope `openid` : sub (obligatoire)
- [ ] Scope `profile` : name, given_name, family_name, middle_name, nickname, preferred_username, profile, picture, website, gender, birthdate, zoneinfo, locale, updated_at
- [ ] Scope `email` : email, email_verified
- [ ] Scope `address` : objet JSON address
- [ ] Scope `phone` : phone_number, phone_number_verified

**Ref:** OpenID Connect Core 1.0 Section 5.3 (UserInfo Endpoint), Section 5.4 (Requesting Claims using Scope Values)
**Labels:** `oidc:core`, `feature:profile`, `type:route`, `priority:critical`, `size:M`
**Dependances:** #7, #20
**Complexite:** M (1 jour)

---

**Issue #32 - Service Profile : CRUD et gestion multi-email**

**Titre:** `feat(profile): service de profil utilisateur et gestion multi-email`

**Description:**
`ProfileService` :
- Get/Update profil (claims OIDC)
- Ajout d'email secondaire avec verification
- Changement d'email principal
- Suppression d'email (pas le principal)
- Upload d'avatar (fichier -> picture_url)

**Criteres d'acceptation:**
- [ ] CRUD profil avec tous les champs OIDC
- [ ] Multi-email : ajout, verification, marquage principal, suppression
- [ ] Upload avatar : validation type MIME, taille max, stockage fichier
- [ ] Retour des claims formattes pour UserInfo

**Ref:** OpenID Connect Core 1.0 Section 5.1 (Standard Claims)
**Labels:** `oidc:core`, `feature:profile`, `type:service`, `priority:high`, `size:M`
**Dependances:** #7
**Complexite:** M (1 jour)

---

**Issue #33 - Page /me : interface utilisateur des parametres de compte**

**Titre:** `feat(auth): pages de parametres utilisateur (profil, securite, sessions, OAuth2)`

**Description:**
Pages HTML pour la gestion du compte :
- /auth/settings : vue d'ensemble (profil, email, MFA status)
- /auth/settings/profile : edition profil
- /auth/settings/emails : gestion multi-email
- /auth/settings/security : changement mot de passe, MFA
- /auth/settings/sessions : liste et revocation
- /auth/settings/apps : clients OAuth2 autorises, revocation d'acces
- API /api/me : endpoint JSON pour SPA

**Criteres d'acceptation:**
- [ ] Templates Jinja2 pour chaque section
- [ ] Authentification requise (session cookie)
- [ ] Liste des sessions actives avec IP et user-agent
- [ ] Liste des clients OAuth2 autorises avec scopes et dates
- [ ] Revocation de session et d'acces client

**Ref:** N/A (interface utilisateur)
**Labels:** `feature:auth`, `feature:profile`, `type:route`, `priority:medium`, `size:L`
**Dependances:** #12, #32
**Complexite:** L (2 jours)

---

**Issue #34 - Password grant type (ROPC) avec support MFA**

**Titre:** `feat(oauth2): grant type password (Resource Owner Password Credentials) avec MFA`

**Description:**
Support du grant_type=password dans le token endpoint :
- Authentification username/password directe
- Support du parametre `otp` pour MFA (TOTP, backup code, email code)
- Emission de tokens (access + refresh + id_token si openid)

Note : Ce grant type est legacy mais necessaire pour certaines applications.

**Criteres d'acceptation:**
- [ ] `username` et `password` requis
- [ ] Authentification via AuthService
- [ ] Si MFA active : `otp` requis, erreur `mfa_required` si absent, `invalid_otp` si invalide
- [ ] Emission token pair avec user_id
- [ ] ID token si scope openid

**Ref:** RFC 6749 Section 4.3 (Resource Owner Password Credentials Grant) - NOTE: deprecated in OAuth 2.1
**Labels:** `rfc:6749`, `feature:oauth2`, `feature:mfa`, `type:route`, `priority:medium`, `size:M`
**Dependances:** #27, #11
**Complexite:** M (1 jour)

---

## M6 - OAuth2 Avance

### EPIC-06: Refresh Token, Revocation, Introspection, Device Code, PAR, JAR, Token Exchange

---

**Issue #35 - Refresh Token grant avec rotation (RFC 6749)**

**Titre:** `feat(oauth2): refresh token grant avec rotation obligatoire`

**Description:**
Support du `grant_type=refresh_token` :
- Validation refresh token (hash, expiration, revocation, non-utilise)
- Rotation : ancien token marque `used_at`, nouveau pair emis
- Scopes demandes doivent etre un sous-ensemble des scopes originaux

**Criteres d'acceptation:**
- [ ] Verification client_id correspond au token
- [ ] Ancien refresh token marque used_at (one-time use = rotation)
- [ ] Nouveau access_token + refresh_token emis
- [ ] Scopes optionnels : sous-ensemble requis
- [ ] Expiration per-client ou globale

**Ref:** RFC 6749 Section 6 (Refreshing an Access Token), Best Current Practice: token rotation
**Labels:** `rfc:6749`, `feature:oauth2`, `type:route`, `priority:critical`, `size:M`
**Dependances:** #27, #21
**Complexite:** M (1 jour)

---

**Issue #36 - Token Revocation (RFC 7009)**

**Titre:** `feat(oauth2): endpoint de revocation de tokens (RFC 7009)`

**Description:**
POST /oauth2/revoke :
- Authentification client requise
- Revocation d'access token (par JTI extrait du JWT) ou refresh token (par hash)
- `token_type_hint` optionnel pour optimiser la recherche
- Retourne toujours 200 OK (meme si token invalide, per RFC 7009)
- Revocation en cascade : refresh token -> tous les access tokens du meme client/user

**Criteres d'acceptation:**
- [ ] Authentification client (Basic ou form-encoded)
- [ ] `token_type_hint=access_token` : essaie JWT d'abord puis refresh
- [ ] `token_type_hint=refresh_token` : essaie refresh d'abord puis JWT
- [ ] Sans hint : essaie access puis refresh
- [ ] 200 OK toujours (RFC 7009 Section 2.2)
- [ ] Revocation cascade refresh -> access tokens

**Ref:** RFC 7009 Section 2 (Token Revocation), Section 2.1 (Revocation Request), Section 2.2 (Revocation Response)
**Labels:** `rfc:7009`, `feature:oauth2`, `type:route`, `priority:critical`, `size:M`
**Dependances:** #20, #27
**Complexite:** M (1 jour)

---

**Issue #37 - Token Introspection (RFC 7662)**

**Titre:** `feat(oauth2): endpoint d'introspection de tokens (RFC 7662)`

**Description:**
POST /oauth2/introspect :
- Authentification client requise + scope `introspect`
- Introspection d'access token (JWT), refresh token (opaque), PAT (prefixe `gab_pat_`)
- Retourne `{"active": false}` pour tout token invalide/expire/revoque
- Retourne les metadonnees pour les tokens actifs

**Criteres d'acceptation:**
- [ ] Authentification client avec scope `introspect` requis
- [ ] Access token : decode JWT sans verification pour JTI, verifie en base
- [ ] Refresh token : verifie hash en base
- [ ] PAT : detection par prefixe `gab_pat_`, validation via PAT service
- [ ] `token_type_hint` pour optimiser la recherche
- [ ] Response : active, scope, client_id, username, token_type, exp, iat, sub, aud, iss, jti

**Ref:** RFC 7662 Section 2 (Introspection Request), Section 2.2 (Introspection Response)
**Labels:** `rfc:7662`, `feature:oauth2`, `type:route`, `priority:high`, `size:L`
**Dependances:** #20, #27
**Complexite:** L (2 jours)

---

**Issue #38 - Modele DeviceCode et service Device Code (RFC 8628)**

**Titre:** `feat(models): modele DeviceCode et service pour Device Authorization (RFC 8628)`

**Description:**
Modele et service pour le Device Code flow :
- `DeviceCode` : device_code_hash, user_code (court, BCDFGHJK), client_id, user_id, scopes, status (pending/authorized/denied/expired), verification_uri, interval, expires_at, last_poll_at
- `DeviceCodeService` : generate, get_by_device_code, get_by_user_code, authorize, deny, is_expired, is_slow_down_required, update_poll_time

**Criteres d'acceptation:**
- [ ] `user_code` : 8 caracteres, format XXXX-XXXX, unique
- [ ] `device_code_hash` : SHA-256, unique
- [ ] Status machine : pending -> authorized/denied
- [ ] `interval` : delai minimum entre polls (defaut 5s)
- [ ] `last_poll_at` : detection slow_down
- [ ] `verification_uri` : URL ou l'utilisateur saisit le user_code

**Ref:** RFC 8628 Section 3.1 (Device Authorization Request), Section 3.2 (Device Authorization Response)
**Labels:** `rfc:8628`, `type:model`, `type:service`, `feature:oauth2`, `priority:high`, `size:L`
**Dependances:** #22
**Complexite:** L (2 jours)

---

**Issue #39 - Endpoints Device Authorization (RFC 8628)**

**Titre:** `feat(oauth2): endpoints Device Authorization flow (RFC 8628)`

**Description:**
Endpoints pour le Device Code flow :
- POST /oauth2/device : device authorization request (retourne device_code, user_code, verification_uri)
- GET /oauth2/device/verify : page de saisie du user_code (formulaire HTML)
- POST /oauth2/device/verify : validation du user_code, redirection vers login puis consentement
- POST /oauth2/device/authorize : approbation/refus par l'utilisateur
- Grant type `urn:ietf:params:oauth:grant-type:device_code` dans le token endpoint

**Criteres d'acceptation:**
- [ ] POST /oauth2/device : retourne device_code, user_code, verification_uri, expires_in, interval
- [ ] verification_uri_complete optionnel (avec user_code pre-rempli)
- [ ] Token endpoint poll : authorization_pending, slow_down, access_denied, expired_token
- [ ] Page HTML de saisie du user_code
- [ ] Flux complet : device request -> user saisit code -> login -> authorize -> device poll -> tokens

**Ref:** RFC 8628 Section 3.1, 3.2, 3.3, 3.4, 3.5
**Labels:** `rfc:8628`, `feature:oauth2`, `type:route`, `priority:high`, `size:XL`
**Dependances:** #27, #38
**Complexite:** XL (3 jours)

---

**Issue #40 - Modele PARRequest et service PAR (RFC 9126)**

**Titre:** `feat(oauth2): Pushed Authorization Requests - modele et service (RFC 9126)`

**Description:**
Modele et service :
- `PARRequest` : request_uri (unique, prefixe `urn:ietf:params:oauth:request_uri:`), client_id (FK), response_type, redirect_uri, scopes, state, code_challenge, code_challenge_method, nonce, prompt, expires_at, used_at
- `PARService` : create_par_request, get_par_request_for_client, mark_as_used, is_expired, is_used

**Criteres d'acceptation:**
- [ ] `request_uri` genere avec prefixe `urn:ietf:params:oauth:request_uri:`
- [ ] Expiration courte (defaut 60s, configurable)
- [ ] One-time use (`used_at`)
- [ ] Validation client au moment de la creation
- [ ] Migration Alembic

**Ref:** RFC 9126 Section 2 (Pushed Authorization Request Endpoint), Section 2.1 (Request), Section 2.2 (Response)
**Labels:** `rfc:9126`, `type:model`, `type:service`, `feature:oauth2`, `priority:high`, `size:M`
**Dependances:** #22, #23
**Complexite:** M (1 jour)

---

**Issue #41 - Endpoint PAR et integration authorize (RFC 9126)**

**Titre:** `feat(oauth2): endpoint POST /oauth2/par et support request_uri dans /authorize (RFC 9126)`

**Description:**
- POST /oauth2/par : reception des parametres d'autorisation, validation, stockage, retourne request_uri + expires_in
- Integration dans GET /oauth2/authorize : si `request_uri` present, charger les parametres depuis PARRequest au lieu des query params
- Verification expiration et usage unique

**Criteres d'acceptation:**
- [ ] POST /oauth2/par : authentification client requise
- [ ] Validation : client_id, redirect_uri, scopes, PKCE
- [ ] Retourne `request_uri` et `expires_in`
- [ ] GET /authorize?client_id=...&request_uri=... : charge depuis PAR
- [ ] PAR expireLe ou deja utilise -> erreur

**Ref:** RFC 9126 Section 2 (PAR Endpoint), Section 4 (Authorization Request using request_uri)
**Labels:** `rfc:9126`, `feature:oauth2`, `type:route`, `priority:high`, `size:M`
**Dependances:** #26, #40
**Complexite:** M (1 jour)

---

**Issue #42 - Service JAR et integration authorize (RFC 9101)**

**Titre:** `feat(oauth2): JWT-Secured Authorization Requests - JAR (RFC 9101)`

**Description:**
`JARService` :
- `validate_request_object(jwt, client, expected_issuer, expected_audience)` : decode et valide le JWT
- `extract_authorization_params(claims, client)` : extrait response_type, redirect_uri, scopes, etc.
- Verification : signature (jwks_uri du client), issuer=client_id, audience=authorization server issuer
- Integration dans GET /authorize : si parametre `request` present, valide le JWT et extrait les parametres

**Criteres d'acceptation:**
- [ ] Decode JWT avec verification signature (cle publique du client via jwks_uri)
- [ ] Verification issuer == client_id
- [ ] Verification audience == issuer du serveur d'autorisation
- [ ] Extraction de tous les parametres d'autorisation depuis les claims
- [ ] Erreurs specifiques : JARError avec error et description
- [ ] `request_object_signing_alg` respecte (defaut RS256)

**Ref:** RFC 9101 Section 4 (Request Object), Section 6.2 (Request Object Validation)
**Labels:** `rfc:9101`, `feature:oauth2`, `type:service`, `type:route`, `priority:medium`, `size:L`
**Dependances:** #26, #23
**Complexite:** L (2 jours)

---

**Issue #43 - Token Exchange (RFC 8693)**

**Titre:** `feat(oauth2): grant type Token Exchange (RFC 8693)`

**Description:**
`TokenExchangeService` et integration token endpoint :
- `validate_subject_token()` : valide le token source (JWT ou opaque)
- `validate_actor_token()` : valide le token acteur (optionnel, pour delegation)
- `determine_scopes()` : scopes du nouveau token (avec escalade possible via RBAC)
- `validate_audience()` : audience/resource cible
- Grant type : `urn:ietf:params:oauth:grant-type:token-exchange`
- Support `act` claim pour la delegation

**Criteres d'acceptation:**
- [ ] `subject_token` et `subject_token_type` requis
- [ ] subject_token_type : `urn:ietf:params:oauth:token-type:access_token`
- [ ] Client confidentiel requis
- [ ] Nouveau access_token emis avec audience cible
- [ ] Support delegation via `act` claim dans le JWT
- [ ] Pas de refresh_token emis pour les token-exchange
- [ ] Erreurs specifiques : TokenExchangeError

**Ref:** RFC 8693 Section 2 (Token Exchange Request), Section 2.1 (Response), Section 4 (Token Type Identifiers)
**Labels:** `rfc:8693`, `feature:oauth2`, `type:service`, `type:route`, `priority:medium`, `size:L`
**Dependances:** #20, #27
**Complexite:** L (2 jours)

---

## M7 - MFA, PAT & RBAC

### EPIC-07: Authentification multi-facteurs

---

**Issue #44 - Modeles MFA : UserMFA, MFABackupCode, MFAEmailCode**

**Titre:** `feat(models): modeles MFA - TOTP, backup codes et codes email`

**Description:**
- `UserMFA` : user_id (unique FK), totp_secret_encrypted (AES-256-GCM), totp_enabled, totp_enabled_at
- `MFABackupCode` : user_mfa_id (FK), code_hash (SHA-256), used_at
- `MFAEmailCode` : user_id (FK), email, code_hash, expires_at, used_at

**Criteres d'acceptation:**
- [ ] Secret TOTP chiffre en AES-256-GCM (pas de clair en base)
- [ ] 10 backup codes par utilisateur, usage unique
- [ ] Codes email avec expiration configurable
- [ ] Relations : UserMFA -> backup_codes (1:N), UserMFA -> User (1:1)

**Ref:** RFC 6238 (TOTP), securite AES-256-GCM
**Labels:** `feature:mfa`, `type:model`, `type:migration`, `priority:high`, `size:M`
**Dependances:** #4
**Complexite:** M (1 jour)

---

**Issue #45 - Service MFA : TOTP setup, verification, backup codes**

**Titre:** `feat(mfa): service TOTP complet avec QR code, backup codes et email fallback`

**Description:**
`MFAService` :
- `setup_totp(user_id, email)` : genere secret, chiffre, retourne URI + QR code base64
- `enable_totp(user_id, code)` : verifie le code, active TOTP, genere backup codes
- `disable_totp(user_id, code)` : verifie le code, desactive, supprime backup codes
- `verify_mfa_code(user_id, code)` : essaie TOTP (6 digits) puis backup code
- `verify_mfa_code_with_email(user_id, code)` : TOTP, backup, puis email code
- `send_mfa_email_code(user_id, email)` : genere et stocke code email
- `regenerate_backup_codes(user_id, code)` : apres verification TOTP

**Criteres d'acceptation:**
- [ ] QR code genere en base64 data URI (PNG)
- [ ] TOTP conforme RFC 6238 (window=1 pour clock drift)
- [ ] Backup codes format XXXX-XXXX, 10 codes, chars non ambigus
- [ ] Verification cascade : TOTP -> backup -> email
- [ ] Encryption/decryption des secrets TOTP via AESEncryption
- [ ] Email fallback : code 6 chiffres, expiration configurable

**Ref:** RFC 6238 (TOTP), RFC 4226 (HOTP base), securite AES-256-GCM
**Labels:** `feature:mfa`, `type:service`, `priority:high`, `size:L`
**Dependances:** #1, #44
**Complexite:** L (2 jours)

---

**Issue #46 - Routes MFA : setup, verify, login challenge 2 etapes**

**Titre:** `feat(mfa): routes MFA setup/verify et login challenge 2 etapes`

**Description:**
- GET /auth/mfa/setup : page de configuration TOTP (QR code)
- POST /auth/mfa/verify : verification du code pour activer TOTP
- POST /auth/mfa/disable : desactivation
- GET/POST /auth/mfa/challenge : page de saisie du code MFA apres login (2eme etape)
- POST /auth/mfa/email : envoi du code MFA par email (fallback)
- Integration dans le flux login : si MFA active, redirect vers /auth/mfa/challenge

**Criteres d'acceptation:**
- [ ] Login en 2 etapes : password OK -> redirect mfa/challenge -> verification code -> session creee
- [ ] Pas de re-saisie du mot de passe (token temporaire entre les 2 etapes)
- [ ] Email fallback : bouton "Recevoir un code par email"
- [ ] Backup code accepte en alternative au TOTP
- [ ] Pages HTML avec templates

**Ref:** N/A (securite MFA, bonnes pratiques NIST SP 800-63B)
**Labels:** `feature:mfa`, `feature:auth`, `type:route`, `priority:high`, `size:L`
**Dependances:** #11, #12, #45
**Complexite:** L (2 jours)

---

### EPIC-08: Personal Access Tokens

---

**Issue #47 - Modele PAT et service PersonalAccessToken**

**Titre:** `feat(pat): modele et service Personal Access Tokens avec prefixe gab_pat_`

**Description:**
Modele `PersonalAccessToken` :
- user_id, name, description, token_hash (SHA-256), token_suffix (4 derniers chars)
- scopes (ARRAY), expires_at (nullable), tenant_id, target_client_id
- last_used_at, last_used_ip, use_count, revoked_at, revoked_by, revocation_reason
- Presets d'expiration : 7, 30, 60, 90, 365 jours, illimitee

Service `PersonalAccessTokenService` :
- create_token, validate_token, revoke_token, list_user_tokens, update_last_used

**Criteres d'acceptation:**
- [ ] Token genere avec prefixe `gab_pat_` + 40 chars random
- [ ] Token affiche une seule fois a la creation
- [ ] Stocke en SHA-256 uniquement
- [ ] `token_suffix` pour identification dans l'UI (****abcd)
- [ ] `validate_token()` : verifie hash, expiration, revocation, met a jour last_used
- [ ] `is_valid` : property combinant !expired et !revoked

**Ref:** N/A (inspire de GitHub Fine-Grained PATs), RFC 7662 (introspection PAT)
**Labels:** `feature:pat`, `type:model`, `type:service`, `priority:high`, `size:L`
**Dependances:** #1, #4
**Complexite:** L (2 jours)

---

### EPIC-09: RBAC

---

**Issue #48 - Modeles RBAC : Scope, Role, RoleScope, UserRole**

**Titre:** `feat(rbac): modeles de controle d'acces par roles - Scope, Role, RoleScope, UserRole`

**Description:**
Modeles :
- `Scope` : name (resource:action), description, resource, action, category (admin/api/custom), is_system, is_active
- `Role` : name, description, is_system. Methode `has_scope()` avec wildcards (*, resource:*)
- `RoleScope` : role_id (FK), scope_id (FK) - table de liaison
- `UserRole` : user_id (FK), role_id (FK), assigned_by, expires_at

Roles systeme par defaut : super_admin, admin, user_manager, client_manager, jwks_admin, security_admin, readonly, operator

**Criteres d'acceptation:**
- [ ] Scopes au format `resource:action` (users:read, clients:write, etc.)
- [ ] Wildcards : `*` (tout), `resource:*` (tout sur une resource)
- [ ] Roles systeme non supprimables (`is_system=true`)
- [ ] `UserRole.expires_at` pour roles temporaires
- [ ] Initialisation des roles et scopes systeme (seed data ou migration)
- [ ] `ADMIN_SCOPES` et `API_SCOPES` dictionnaires pour documentation

**Ref:** N/A (architecture RBAC)
**Labels:** `feature:rbac`, `type:model`, `type:migration`, `priority:high`, `size:L`
**Dependances:** #3, #4
**Complexite:** L (2 jours)

---

**Issue #49 - Dependance d'autorisation RBAC pour les routes admin**

**Titre:** `feat(rbac): middleware d'autorisation RBAC pour les routes d'administration`

**Description:**
Dependance FastAPI pour verifier les permissions :
- `require_role(scope: str)` : verifie que l'utilisateur a le scope requis
- Resolution : User -> UserRole -> Role -> RoleScope -> Scope
- Support wildcards dans la verification
- Integration avec le systeme de session (cookie) et Bearer token (API)

**Criteres d'acceptation:**
- [ ] `Depends(require_role("users:read"))` sur les routes admin
- [ ] Verification en cascade : role wildcards resolus
- [ ] 403 Forbidden si scope manquant
- [ ] Support authentification par session ET par Bearer token
- [ ] Roles expires exclus

**Ref:** N/A (architecture)
**Labels:** `feature:rbac`, `type:infra`, `priority:high`, `size:M`
**Dependances:** #48, #12
**Complexite:** M (1 jour)

---

## M8 - Multi-tenancy, Federation & Ops

### EPIC-10: Multi-tenancy

---

**Issue #50 - Modele Tenant et TenantMember**

**Titre:** `feat(tenant): modeles Tenant, TenantMember et TenantCustomRole`

**Description:**
- `Tenant` : slug (unique), display_name, custom_domain, custom_domain_status, is_active, is_platform, settings (JSONB), trust_mode
- `TenantCustomRole` : tenant_id, name (unique per tenant), display_name, description, scopes (ARRAY), is_system, display_order
- `TenantMember` : tenant_id + user_id (unique), role_id (FK), invited_by, invited_at, joined_at
- Roles par defaut : Owner (*), Admin (sous-ensemble), Member (members:read)
- TENANT_SCOPES dict pour les permissions

**Criteres d'acceptation:**
- [ ] `slug` max 63 chars (RFC subdomain), unique
- [ ] `is_platform` : un seul tenant peut etre la plateforme
- [ ] `trust_mode` : none, all, members_only, specific
- [ ] `TenantCustomRole.has_scope()` avec wildcards
- [ ] `TenantMember.role_name` et `role_display_name` comme proprietes
- [ ] `DEFAULT_TENANT_ROLES` crees automatiquement pour chaque nouveau tenant

**Ref:** N/A (architecture multi-tenant)
**Labels:** `feature:tenant`, `type:model`, `type:migration`, `priority:high`, `size:L`
**Dependances:** #3, #4
**Complexite:** L (2 jours)

---

**Issue #51 - Middleware de resolution de tenant**

**Titre:** `feat(tenant): middleware de resolution de tenant (subdomain, path, custom domain)`

**Description:**
`TenantMiddleware` :
- Resolution par sous-domaine (slug.base_domain)
- Resolution par path (/t/{slug}/...)
- Resolution par domaine personnalise (CNAME lookup en base)
- Context tenant stocke dans ContextVar (thread-safe)
- Cookie de session scope par tenant

**Criteres d'acceptation:**
- [ ] `get_tenant_context()` retourne TenantContext (tenant_id, slug, resolution_method)
- [ ] Subdomain : extrait slug depuis Host header
- [ ] Path : strip /t/{slug}/ du path, set context
- [ ] Custom domain : lookup en base
- [ ] Cookie name scope : `session_{slug}` ou `session` (global)

**Ref:** N/A (architecture multi-tenant)
**Labels:** `feature:tenant`, `type:infra`, `priority:high`, `size:L`
**Dependances:** #50
**Complexite:** L (2 jours)

---

**Issue #52 - Domaines personnalises avec CNAME, Nginx et Certbot**

**Titre:** `feat(tenant): domaines personnalises avec validation CNAME, config Nginx et SSL Certbot`

**Description:**
Modele et service pour les domaines personnalises :
- `CustomDomainStatus` : pending -> dns_verifying -> dns_verified -> ssl_provisioning -> active/failed
- Tache Celery de verification DNS (CNAME)
- Generation config Nginx automatique
- Provisioning SSL via Certbot
- Tache periodique de re-verification

**Criteres d'acceptation:**
- [ ] Machine d'etat de provisioning complete
- [ ] Verification CNAME pointe vers `cname_target`
- [ ] Template Nginx genere et installe
- [ ] Certbot lance en tache Celery
- [ ] `custom_domain_checked_at` pour tracking

**Ref:** N/A (operations)
**Labels:** `feature:tenant`, `type:service`, `type:infra`, `priority:medium`, `size:XL`
**Dependances:** #50, #51
**Complexite:** XL (3 jours)

---

**Issue #53 - Branding par tenant (couleurs, logos, templates)**

**Titre:** `feat(tenant): branding par tenant - TenantBranding et TenantTemplate`

**Description:**
- `TenantBranding` : tenant_id (1:1), logo_url, logo_dark_url, favicon_url, couleurs (primary, secondary, accent, background, surface, text, etc.), font_family, font_url, custom_css, custom_js, show_powered_by
- `TenantTemplate` : tenant_id + template_name (unique), content (Jinja2), is_active
- `BrandingService` : `render_template(db, template_name, context, tenant_id)` avec fallback sur les templates par defaut si pas de template custom

**Criteres d'acceptation:**
- [ ] Surcharge de templates par tenant (login, register, consent, etc.)
- [ ] CSS variables injectees depuis TenantBranding
- [ ] Fallback sur templates par defaut si pas de custom
- [ ] Templates custom stockes en base (pas de fichier)
- [ ] Couleurs completes (12+ variables de couleur)

**Ref:** N/A (UX multi-tenant)
**Labels:** `feature:tenant`, `type:model`, `type:service`, `priority:medium`, `size:L`
**Dependances:** #50
**Complexite:** L (2 jours)

---

**Issue #54 - Trust policy et sources de confiance**

**Titre:** `feat(tenant): politique de confiance et TenantTrustedSource`

**Description:**
- `TenantTrustedSource` : tenant_id + trusted_tenant_id (unique), description
- Trust modes : none (propres users), all (ouvert), members_only, specific (liste de tenants)
- Verification dans le flux de login

**Criteres d'acceptation:**
- [ ] Trust mode configurable par tenant
- [ ] `specific` : seuls les users des tenants listes peuvent se connecter
- [ ] `trusted_tenant_id=NULL` signifie "domaine principal"
- [ ] Integration dans le flux d'authentification

**Ref:** N/A (securite multi-tenant)
**Labels:** `feature:trust`, `feature:tenant`, `type:model`, `type:service`, `priority:medium`, `size:M`
**Dependances:** #50
**Complexite:** M (1 jour)

---

### EPIC-11: Federation / Social Login

---

**Issue #55 - Modeles IdentityProvider et FederatedIdentity**

**Titre:** `feat(federation): modeles IdentityProvider et FederatedIdentity pour social login`

**Description:**
- `IdentityProvider` : tenant_id, name, provider_type (oidc/google/github/microsoft), discovery_url, endpoints, client_id, client_secret_encrypted, scopes, attribute_mapping (JSONB), allowed_domains, auto_provision, allow_linking, display settings
- `FederatedIdentity` : user_id + idp_id (unique on external_subject), external_subject, external_email, raw_claims (JSONB), linked_at, last_login_at

**Criteres d'acceptation:**
- [ ] Support Google, GitHub, Microsoft/Azure AD, OIDC generique
- [ ] `client_secret_encrypted` en AES-256-GCM
- [ ] `attribute_mapping` configurable (mapping des claims externes vers internes)
- [ ] `allowed_domains` pour restreindre par domaine email
- [ ] `auto_provision` : creation automatique d'utilisateur au premier login
- [ ] `allow_linking` : lier un compte existant automatiquement par email

**Ref:** OpenID Connect Core 1.0 (upstream IdP), RFC 6749 (OAuth2 client vers IdP externe)
**Labels:** `feature:federation`, `oidc:core`, `type:model`, `type:migration`, `priority:medium`, `size:M`
**Dependances:** #50, #1
**Complexite:** M (1 jour)

---

**Issue #56 - Service et routes de Federation/Social Login**

**Titre:** `feat(federation): service de social login avec auto-linking et claim mapping`

**Description:**
`FederationService` :
- Initiation du flux OAuth2 vers l'IdP externe
- Callback : echange code, recup userinfo, mapping claims, auto-provision ou linking
- Routes : GET /federation/{provider}/login, GET /federation/{provider}/callback
- Support OIDC discovery (decouverte automatique des endpoints)
- Mapping des claims configurables par IdP

**Criteres d'acceptation:**
- [ ] Flux complet : redirect vers IdP -> callback -> creation/linking user -> session
- [ ] Auto-provision : cree User + UserEmail si nouveau
- [ ] Auto-linking : lie au user existant par email si `allow_linking=true`
- [ ] Claim mapping : email, name, given_name, family_name via `attribute_mapping`
- [ ] Google : endpoints hardcodes ou via discovery
- [ ] GitHub : OAuth2 (pas OIDC pur), endpoint userinfo specifique
- [ ] Microsoft : support Azure AD avec tenant configurale

**Ref:** OpenID Connect Core 1.0 Section 3 (Authentication using Authorization Code Flow)
**Labels:** `feature:federation`, `oidc:core`, `type:service`, `type:route`, `priority:medium`, `size:XL`
**Dependances:** #55, #9, #12
**Complexite:** XL (3 jours)

---

### EPIC-12: Administration

---

**Issue #57 - Routes d'administration : Users CRUD**

**Titre:** `feat(admin): administration des utilisateurs - CRUD, activation, memberships`

**Description:**
- GET /admin/users : liste paginee avec recherche
- GET /admin/users/{id} : detail avec emails, roles, sessions, memberships tenant
- POST /admin/users/{id}/activate et /deactivate
- DELETE /admin/users/{id}
- Double interface : pages HTML (Jinja2) + API JSON
- Protection RBAC (scope `users:*`)

**Criteres d'acceptation:**
- [ ] Liste paginee avec filtre par nom/email
- [ ] Detail : infos, emails, roles, sessions actives, memberships tenant
- [ ] Activation/desactivation
- [ ] Suppression (cascade)
- [ ] HTML + JSON (content negotiation ou routes separees)
- [ ] RBAC : scopes users:read, users:write, users:disable, users:delete

**Ref:** N/A (administration)
**Labels:** `feature:admin`, `type:route`, `priority:medium`, `size:L`
**Dependances:** #4, #48, #49
**Complexite:** L (2 jours)

---

**Issue #58 - Routes d'administration : Clients OAuth2 CRUD**

**Titre:** `feat(admin): administration des clients OAuth2 - CRUD, rotation secret, config`

**Description:**
- CRUD complet des clients OAuth2
- Rotation de secret
- Configuration PKCE, consentement, JAR
- Gestion des redirect_uris, scopes, grant_types
- RBAC scope `clients:*`

**Criteres d'acceptation:**
- [ ] Creation avec generation client_id et client_secret
- [ ] Rotation de secret (nouveau genere, ancien invalide)
- [ ] Configuration : require_pkce, require_consent, jwks_uri
- [ ] Gestion des allowed_origins (CORS)
- [ ] Custom token expiry par client
- [ ] HTML + JSON

**Ref:** RFC 6749 Section 2 (Client Registration)
**Labels:** `feature:admin`, `rfc:6749`, `type:route`, `priority:medium`, `size:L`
**Dependances:** #22, #23, #49
**Complexite:** L (2 jours)

---

**Issue #59 - Routes d'administration : Sessions, JWKS, Roles, PATs, Tenants**

**Titre:** `feat(admin): administration sessions, JWKS, roles/scopes, PATs et tenants`

**Description:**
Routes d'administration pour les entites restantes :
- Sessions : listing, detail, revocation individuelle et bulk
- JWKS : generation, activation, revocation, rotation, suppression
- Roles & Scopes : CRUD roles custom, gestion scopes, assignation
- PATs : monitoring, revocation
- Tenants : CRUD, branding, domaines custom, membres, roles tenant
- Dashboard avec metriques

**Criteres d'acceptation:**
- [ ] Chaque entite : liste, detail, actions
- [ ] RBAC par scope (sessions:*, jwks:*, roles:*, pats:*, etc.)
- [ ] Dashboard : nombre d'utilisateurs, sessions actives, tokens
- [ ] HTML + JSON pour chaque route

**Ref:** N/A (administration)
**Labels:** `feature:admin`, `type:route`, `priority:medium`, `size:XL`
**Dependances:** #12, #18, #48, #47, #50
**Complexite:** XL (3 jours)

---

### EPIC-13: Taches planifiees et maintenance

---

**Issue #60 - Taches Celery Beat de nettoyage**

**Titre:** `feat(cleanup): taches Celery Beat de nettoyage des donnees expirees`

**Description:**
Taches planifiees Celery :
- `cleanup_expired_tokens` : access + refresh tokens (1h)
- `cleanup_expired_authorization_codes` : (15min)
- `cleanup_expired_device_codes` : (30min)
- `cleanup_expired_par_requests` : (15min)
- `cleanup_expired_verification_codes` : (1h)
- `cleanup_expired_password_reset_tokens` : (1h)
- `cleanup_expired_mfa_email_codes` : (30min)
- `cleanup_expired_sessions` : (quotidien)
- `cleanup_expired_pats` : (quotidien, grace period 30j expire / 90j revoque)
- `cleanup_orphaned_avatars` : (quotidien)
- `cleanup_unverified_users` : (quotidien, apres N jours)

**Criteres d'acceptation:**
- [ ] Chaque tache utilise une session DB synchrone (Celery worker)
- [ ] Delete en masse avec WHERE conditions
- [ ] Logging du nombre d'enregistrements supprimes
- [ ] Retour dict avec compteurs
- [ ] Celery Beat schedule configure

**Ref:** N/A (operations, hygiene base de donnees)
**Labels:** `feature:cleanup`, `type:service`, `type:infra`, `priority:medium`, `size:L`
**Dependances:** #21, #24, #38, #40, #5, #6, #44, #47
**Complexite:** L (2 jours)

---

**Issue #61 - Tache Celery de provisioning domaines custom**

**Titre:** `feat(tenant): tache Celery de verification DNS et provisioning SSL pour domaines custom`

**Description:**
- Tache periodique : verifie les domaines en status `pending` ou `dns_verifying`
- Verification CNAME via DNS
- Generation config Nginx
- Lancement Certbot pour SSL
- Mise a jour du status

**Criteres d'acceptation:**
- [ ] Verification DNS avec `dns.resolver`
- [ ] Mise a jour status dans la machine d'etat
- [ ] Config Nginx generee depuis template
- [ ] Certbot lance en subprocess
- [ ] Retry et error tracking

**Ref:** N/A (operations)
**Labels:** `feature:tenant`, `type:service`, `priority:low`, `size:L`
**Dependances:** #52
**Complexite:** L (2 jours)

---

**Issue #62 - Templates email MJML avec branding tenant**

**Titre:** `feat(email): templates MJML pour verification, reset, MFA et bienvenue avec branding tenant`

**Description:**
Templates MJML :
- Verification email
- Reset password
- Code MFA par email
- Bienvenue apres verification
- Integration du branding tenant (couleurs, logo)
- Rendu MJML -> HTML

**Criteres d'acceptation:**
- [ ] 4 templates minimum
- [ ] Variables de branding injectees (couleurs, logo, nom tenant)
- [ ] Fallback texte (templates .txt)
- [ ] Responsive (MJML)

**Ref:** N/A (UX)
**Labels:** `feature:email`, `type:infra`, `priority:medium`, `size:M`
**Dependances:** #17, #53
**Complexite:** M (1 jour)

---

**Issue #63 - Routes PAT utilisateur : creation, liste, revocation**

**Titre:** `feat(pat): routes utilisateur pour la gestion des Personal Access Tokens`

**Description:**
- POST /auth/settings/pats : creation PAT (retourne token une seule fois)
- GET /auth/settings/pats : liste des PATs de l'utilisateur
- DELETE /auth/settings/pats/{id} : revocation
- Interface HTML dans les parametres utilisateur

**Criteres d'acceptation:**
- [ ] Token affiche une seule fois dans la reponse de creation
- [ ] Liste : nom, suffix, scopes, derniere utilisation, expiration
- [ ] Revocation avec motif optionnel
- [ ] Formulaire de creation avec choix d'expiration et scopes

**Ref:** N/A
**Labels:** `feature:pat`, `type:route`, `priority:medium`, `size:M`
**Dependances:** #47, #12
**Complexite:** M (1 jour)

---

---

## Ordre de dependance global (chemin critique)

```
Phase 1 (M1) - Semaine 1-2:
  #1 Security -> #2 Config -> #3 DB Base
  #3 -> #4 User models -> #5 VerificationCode -> #6 Session -> #7 UserProfile
  #8 CORS

Phase 2 (M2) - Semaine 2-3:
  #4 -> #9 Registration -> #10 Verification
  #4 -> #11 Login -> #12 Session service -> #13 Logout
  #5 -> #14 Password reset, #15 Change password
  #16 Dependencies, #17 Email service

Phase 3 (M3) - Semaine 3-4:
  #1,#3 -> #18 JWKS model+service -> #19 JWKS endpoint
  #18 -> #20 Token service -> #21 Token models

Phase 4 (M4) - Semaine 4-5:
  #3 -> #22 OAuth2Client model -> #23 Client service -> #24 AuthCode model
  #25 PKCE service
  #11,#12,#23,#24,#25 -> #26 Authorize endpoint
  #20,#21,#23 -> #27 Token endpoint
  #26 -> #28 Consent screen
  #29 Issuer service

Phase 5 (M5) - Semaine 5-6:
  #29 -> #30 Discovery endpoint
  #7,#20 -> #31 UserInfo
  #7 -> #32 Profile service -> #33 Settings pages
  #27,#11 -> #34 Password grant

Phase 6 (M6) - Semaine 6-8:
  #27 -> #35 Refresh token, #36 Revocation, #37 Introspection
  #22 -> #38 DeviceCode model/service -> #39 DeviceCode endpoints
  #22 -> #40 PAR model/service -> #41 PAR endpoint
  #26 -> #42 JAR service
  #20,#27 -> #43 Token Exchange

Phase 7 (M7) - Semaine 8-10:
  #4 -> #44 MFA models -> #45 MFA service -> #46 MFA routes
  #4 -> #47 PAT model+service -> #63 PAT routes
  #3,#4 -> #48 RBAC models -> #49 RBAC middleware

Phase 8 (M8) - Semaine 10-13:
  #3,#4 -> #50 Tenant models -> #51 Tenant middleware -> #52 Custom domains
  #50 -> #53 Branding, #54 Trust policy
  #50 -> #55 Federation models -> #56 Federation routes
  #49 -> #57 Admin Users -> #58 Admin Clients -> #59 Admin All
  #60 Cleanup tasks, #61 Domain provisioning, #62 Email templates
```

---

## Recapitulatif des estimations

| Taille | Duree estimee | Nombre d'issues |
|--------|---------------|-----------------|
| S (Small) | 0.5 jour | 14 |
| M (Medium) | 1 jour | 23 |
| L (Large) | 2 jours | 19 |
| XL (Extra Large) | 3 jours | 7 |
| **Total** | | **63 issues** |

**Effort total estime : ~85 jours-developpeur** (environ 17 semaines a un rythme normal, ou 8.5 semaines a 2 developpeurs).

---

## Notes sur la creation des issues via `gh`

Chaque issue doit etre creee avec :
```bash
gh issue create --repo goabonga/shomer \
  --title "feat(scope): titre en francais" \
  --body "..." \
  --label "rfc:XXXX,feature:xxx,type:xxx,size:X,priority:xxx" \
  --milestone "M1 - Fondations & Securite"
```

Les milestones doivent etre crees en premier :
```bash
gh api repos/goabonga/shomer/milestones -f title="M1 - Fondations & Sécurité" -f description="Infrastructure crypto, modèles de base, configuration"
```

Les labels doivent etre crees en premier :
```bash
gh label create "rfc:6749" --color "0E8A16" --description "RFC 6749 - OAuth 2.0 Authorization Framework"
```

---

### Critical Files for Implementation

These are the key reference files from the auth project that the implementor will need to consult most frequently:

- `/home/goabonga/refacto/auth/app/core/security.py` - The foundational security module (Argon2id, AES-256-GCM) that must be replicated first as everything depends on it
- `/home/goabonga/refacto/auth/app/db/models/oauth2.py` - The most complex model file containing OAuth2Client, AuthorizationCode, AccessToken, RefreshToken, DeviceCode, PARRequest -- the core of the OAuth2 data layer
- `/home/goabonga/refacto/auth/app/api/routes/oauth2/token.py` - The token endpoint handling all 6 grant types -- the central hub of the OAuth2 protocol implementation
- `/home/goabonga/refacto/auth/app/db/models/tenant.py` - The multi-tenancy model file with Tenant, TenantMember, IdentityProvider, FederatedIdentity, TenantBranding, TenantTemplate -- the most table-rich model file
- `/home/goabonga/refacto/shomer/src/shomer/app.py` - The target project's current entry point, which will need to be extended with all new routers, middleware, and lifespan logic