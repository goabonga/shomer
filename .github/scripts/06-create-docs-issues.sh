#!/bin/bash
set -euo pipefail

REPO="${1:-goabonga/shomer}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ISSUES_DIR="$(dirname "$SCRIPT_DIR")/issues"

echo "=== Creating M20-M23 issues for $REPO ==="
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
# M20 - CLI Administration (GH #102-111)
# ============================================================

create_issue "M20-cli/102-cli-framework-typer.md" \
    "feat(cli): Typer framework with API client and authentication" \
    "M20 - CLI Administration" \
    "type:infra,size:M"

create_issue "M20-cli/103-cli-seed.md" \
    "feat(cli): shomer seed — initial data seeding (superadmin, roles, scopes, client)" \
    "M20 - CLI Administration" \
    "type:infra,feature:rbac,size:M"

create_issue "M20-cli/104-cli-user.md" \
    "feat(cli): shomer user — user management commands" \
    "M20 - CLI Administration" \
    "feature:admin,feature:auth,size:M"

create_issue "M20-cli/105-cli-client.md" \
    "feat(cli): shomer client — OAuth2 client management commands" \
    "M20 - CLI Administration" \
    "feature:admin,feature:oauth2,rfc:6749,size:M"

create_issue "M20-cli/106-cli-session.md" \
    "feat(cli): shomer session — session management commands" \
    "M20 - CLI Administration" \
    "feature:admin,feature:session,size:S"

create_issue "M20-cli/107-cli-jwks.md" \
    "feat(cli): shomer jwks — key management commands" \
    "M20 - CLI Administration" \
    "feature:admin,feature:jwks,rfc:7517,size:M"

create_issue "M20-cli/108-cli-role-scope.md" \
    "feat(cli): shomer role/scope — RBAC management commands" \
    "M20 - CLI Administration" \
    "feature:admin,feature:rbac,size:M"

create_issue "M20-cli/109-cli-tenant.md" \
    "feat(cli): shomer tenant — tenant management commands" \
    "M20 - CLI Administration" \
    "feature:admin,feature:tenant,size:L"

create_issue "M20-cli/110-cli-pat.md" \
    "feat(cli): shomer pat — PAT management commands" \
    "M20 - CLI Administration" \
    "feature:admin,feature:pat,size:S"

create_issue "M20-cli/111-cli-token.md" \
    "feat(cli): shomer token — token operations commands" \
    "M20 - CLI Administration" \
    "feature:admin,rfc:7009,rfc:7662,size:M"

# ============================================================
# M21 - Documentation (GH #112-125)
# ============================================================

create_issue "M21-documentation/112-docs-architecture.md" \
    "docs(architecture): system architecture and design decisions" \
    "M21 - Documentation" \
    "type:docs,size:L"

create_issue "M21-documentation/113-docs-config-reference.md" \
    "docs(config): complete configuration reference" \
    "M21 - Documentation" \
    "type:docs,size:M"

create_issue "M21-documentation/114-docs-api-reference.md" \
    "docs(api): OpenAPI/Swagger auto-generated API reference" \
    "M21 - Documentation" \
    "type:docs,layer:api,size:L"

create_issue "M21-documentation/115-docs-oauth2-flows.md" \
    "docs(oauth2): OAuth2 authorization flows integration guide" \
    "M21 - Documentation" \
    "type:docs,rfc:6749,feature:oauth2,size:XL"

create_issue "M21-documentation/116-docs-oidc-integration.md" \
    "docs(oidc): OpenID Connect integration guide" \
    "M21 - Documentation" \
    "type:docs,oidc:core,oidc:discovery,size:L"

create_issue "M21-documentation/117-docs-mfa-guide.md" \
    "docs(mfa): MFA setup and administration guide" \
    "M21 - Documentation" \
    "type:docs,feature:mfa,size:M"

create_issue "M21-documentation/118-docs-multitenancy-guide.md" \
    "docs(multitenancy): multi-tenancy and custom domains guide" \
    "M21 - Documentation" \
    "type:docs,feature:tenant,size:L"

create_issue "M21-documentation/119-docs-federation-guide.md" \
    "docs(federation): identity federation and social login configuration" \
    "M21 - Documentation" \
    "type:docs,feature:federation,size:M"

create_issue "M21-documentation/120-docs-rbac-guide.md" \
    "docs(rbac): RBAC and access control guide" \
    "M21 - Documentation" \
    "type:docs,feature:rbac,size:M"

create_issue "M21-documentation/121-docs-pat-guide.md" \
    "docs(pat): Personal Access Tokens usage guide" \
    "M21 - Documentation" \
    "type:docs,feature:pat,size:S"

create_issue "M21-documentation/122-docs-deployment-hardening.md" \
    "docs(deployment): production deployment and security hardening" \
    "M21 - Documentation" \
    "type:docs,type:infra,size:L"

create_issue "M21-documentation/123-docs-sdk-examples.md" \
    "docs(sdk): client integration examples (Python, JavaScript, Go, cURL)" \
    "M21 - Documentation" \
    "type:docs,feature:oauth2,size:L"

create_issue "M21-documentation/124-docs-database-migrations.md" \
    "docs(database): database schema and migrations guide" \
    "M21 - Documentation" \
    "type:docs,type:migration,size:S"

create_issue "M21-documentation/125-docs-troubleshooting.md" \
    "docs(troubleshooting): troubleshooting guide and FAQ" \
    "M21 - Documentation" \
    "type:docs,size:M"

# ============================================================
# M22 - Terraform Provider (GH #126-133)
# ============================================================

create_issue "M22-terraform/126-terraform-provider-scaffold.md" \
    "feat(terraform): Terraform provider scaffold and authentication" \
    "M22 - Terraform Provider" \
    "type:infra,size:L"

create_issue "M22-terraform/127-terraform-resource-user.md" \
    "feat(terraform): resource shomer_user" \
    "M22 - Terraform Provider" \
    "feature:admin,feature:auth,size:M"

create_issue "M22-terraform/128-terraform-resource-client.md" \
    "feat(terraform): resource shomer_oauth2_client" \
    "M22 - Terraform Provider" \
    "feature:admin,feature:oauth2,rfc:6749,size:L"

create_issue "M22-terraform/129-terraform-resource-role-scope.md" \
    "feat(terraform): resources shomer_role, shomer_scope, shomer_role_scope_assignment" \
    "M22 - Terraform Provider" \
    "feature:admin,feature:rbac,size:L"

create_issue "M22-terraform/130-terraform-resource-tenant.md" \
    "feat(terraform): resource shomer_tenant and related resources" \
    "M22 - Terraform Provider" \
    "feature:admin,feature:tenant,size:XL"

create_issue "M22-terraform/131-terraform-resource-idp.md" \
    "feat(terraform): resource shomer_identity_provider" \
    "M22 - Terraform Provider" \
    "feature:admin,feature:federation,size:M"

create_issue "M22-terraform/132-terraform-resource-jwks.md" \
    "feat(terraform): resource shomer_jwk and data source shomer_jwks" \
    "M22 - Terraform Provider" \
    "feature:admin,feature:jwks,rfc:7517,size:M"

create_issue "M22-terraform/133-terraform-datasources.md" \
    "feat(terraform): data sources (user, client, role, scope, tenant)" \
    "M22 - Terraform Provider" \
    "feature:admin,size:M"

# ============================================================
# M23 - Kubernetes Operator (GH #134-140)
# ============================================================

create_issue "M23-k8s-operator/134-k8s-operator-scaffold.md" \
    "feat(k8s): Kubernetes operator scaffold with controller-runtime" \
    "M23 - Kubernetes Operator" \
    "type:infra,size:L"

create_issue "M23-k8s-operator/135-k8s-crd-oauth2client.md" \
    "feat(k8s): CRD ShomerOAuth2Client" \
    "M23 - Kubernetes Operator" \
    "feature:admin,feature:oauth2,rfc:6749,size:L"

create_issue "M23-k8s-operator/136-k8s-crd-user.md" \
    "feat(k8s): CRD ShomerUser" \
    "M23 - Kubernetes Operator" \
    "feature:admin,feature:auth,size:M"

create_issue "M23-k8s-operator/137-k8s-crd-tenant.md" \
    "feat(k8s): CRD ShomerTenant" \
    "M23 - Kubernetes Operator" \
    "feature:admin,feature:tenant,size:XL"

create_issue "M23-k8s-operator/138-k8s-crd-role-scope.md" \
    "feat(k8s): CRDs ShomerRole, ShomerScope" \
    "M23 - Kubernetes Operator" \
    "feature:admin,feature:rbac,size:L"

create_issue "M23-k8s-operator/139-k8s-crd-idp.md" \
    "feat(k8s): CRD ShomerIdentityProvider" \
    "M23 - Kubernetes Operator" \
    "feature:admin,feature:federation,size:M"

create_issue "M23-k8s-operator/140-k8s-helm-operator.md" \
    "feat(k8s): Helm chart for Shomer operator deployment" \
    "M23 - Kubernetes Operator" \
    "type:infra,size:M"

echo ""
echo "=== All 39 issues created (10 CLI + 14 docs + 8 Terraform + 7 K8s) for $REPO ==="
