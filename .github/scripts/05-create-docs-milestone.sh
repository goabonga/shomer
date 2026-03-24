#!/bin/bash
set -euo pipefail

REPO="${1:-goabonga/shomer}"

echo "=== Creating M20-M23 milestones for $REPO ==="

gh api repos/$REPO/milestones -f title="M20 - CLI Administration" \
  -f description="Typer-based CLI client for administering Shomer via its APIs: users, clients, sessions, JWKS, RBAC, tenants, PATs, tokens." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M21 - Documentation" \
  -f description="Architecture, configuration reference, integration guides, API docs, SDK examples, troubleshooting." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M22 - Terraform Provider" \
  -f description="Terraform provider for managing Shomer resources as code: users, clients, roles, scopes, tenants, IdPs, JWKS." \
  -f state="open"

gh api repos/$REPO/milestones -f title="M23 - Kubernetes Operator" \
  -f description="Kubernetes operator with CRDs for managing Shomer resources via kubectl/GitOps: OAuth2Client, User, Tenant, Role, Scope, IdP." \
  -f state="open"

echo "=== M20-M23 milestones created ($REPO) ==="
