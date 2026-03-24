# GOABONGA Auth — Liste complète des features

Service OIDC/OAuth2 en Python/FastAPI.

---

## 1. Authentification utilisateur
- Inscription par email avec vérification par code
- Login par formulaire et API
- Déconnexion (session unique ou toutes les sessions)
- Mot de passe oublié / réinitialisation par token
- Changement de mot de passe (avec vérification de l'ancien)
- Historique des mots de passe (Argon2id)

## 2. Authentification multi-facteurs (MFA)
- **TOTP** — setup avec QR code, vérification, activation/désactivation
- **Backup codes** — génération de 10 codes, usage unique, régénération
- **Email MFA** — envoi de code par email comme fallback
- **Login challenge 2 étapes** — MFA sans re-saisie du mot de passe
- Secrets TOTP chiffrés en AES-256-GCM

## 3. OAuth2 / OpenID Connect
- **Authorization Code** avec PKCE (obligatoire par défaut)
- **Client Credentials** grant
- **Refresh Token** grant avec rotation
- **Device Code** flow (RFC 8628) pour IoT/TV
- **Token Exchange** (RFC 8693)
- **Pushed Authorization Requests (PAR)** — RFC 9126
- **JWT Authorization Request (JAR)** — RFC 9101
- Token revocation (RFC 7009) et introspection (RFC 7662)
- Écran de consentement utilisateur
- Endpoint **UserInfo** (GET/POST)

## 4. Discovery & JWKS
- `/.well-known/openid-configuration` — métadonnées OIDC
- `/.well-known/jwks.json` — clés publiques RSA
- Rotation de clés (90 jours par défaut), activation/révocation
- Gestion des clés de chiffrement AES-256-GCM

## 5. Gestion des sessions
- Création, validation, révocation
- Sessions avec sliding window (extension automatique)
- CSRF tokens
- Suivi IP + user agent
- Sessions scopées par tenant
- Révocation individuelle ou en masse

## 6. Personal Access Tokens (PAT)
- Génération avec préfixe `gab_pat_`
- Expiration configurable (7, 30, 60, 90, 365 jours ou illimitée)
- Scopes d'accès, révocation, introspection

## 7. RBAC (Contrôle d'accès par rôles)
- Rôles système : `super_admin`, `admin`, `user_manager`, `client_manager`, `jwks_admin`, `security_admin`, `readonly`, `operator`
- Scopes au format `resource:action`
- Création de rôles et scopes personnalisés
- Attribution rôles → utilisateurs, scopes → rôles

## 8. Multi-tenancy
- Création et gestion de tenants (organisations)
- Résolution par sous-domaine
- **Domaines personnalisés** avec validation CNAME, auto-config Nginx + Certbot SSL
- Branding par tenant (couleurs, logos, CSS, favicon)
- Templates d'emails par tenant
- Rôles tenant : Owner, Admin, Member + rôles custom
- Sessions et clients OAuth2 scopés par tenant

## 9. Fédération / Social Login
- **Google**, **GitHub**, **Microsoft/Azure AD** OAuth2
- Support OIDC générique pour tout IdP
- Création/linking automatique au premier login
- Mapping de claims email et profil

## 10. Profil utilisateur
- Champs OIDC complets (name, given_name, family_name, nickname, birthdate, locale, gender, etc.)
- Adresse postale structurée
- Téléphone avec flag de vérification
- Upload d'avatar
- Gestion multi-emails (ajout, vérification, email principal, suppression)

## 11. Administration
- **Users** — CRUD, activation/désactivation, suppression, détail avec memberships tenant
- **Clients OAuth2** — CRUD, rotation de secret, config PKCE/consentement/JAR
- **Sessions** — listing, détail, révocation
- **JWKS** — génération, activation, révocation, rotation bulk
- **Rôles & Scopes** — gestion complète
- **PATs** — monitoring, révocation
- **Tenants** — CRUD, branding, domaines custom, membres, rôles
- Double interface : pages HTML (Jinja2) + API JSON

## 12. Emails
- Backends : SMTP (aiosmtplib) ou service Mailler (authentifié OAuth2)
- Envoi async via Celery (retry x3)
- Templates MJML : vérification, reset password, MFA, bienvenue
- Branding personnalisé par tenant

## 13. Trust & Device Verification
- Politique de confiance (remember device/browser)
- Gestion des sources de confiance (IP)
- Endpoints de vérification

## 14. Tâches planifiées (Celery Beat)
- Nettoyage tokens expirés (1h)
- Nettoyage authorization codes (15min)
- Nettoyage device codes (30min)
- Nettoyage PAR requests (15min)
- Nettoyage verification codes (1h)
- Nettoyage password reset tokens (1h)
- Nettoyage MFA email codes (30min)
- Nettoyage sessions expirées (quotidien)

## 15. Sécurité
- Argon2id (mots de passe), SHA-256 (tokens en BDD)
- JWT signés RSA-2048
- AES-256-GCM (secrets TOTP, clés privées)
- CSRF, cookies sécurisés, CORS
- Support systemd-creds pour les secrets en production
