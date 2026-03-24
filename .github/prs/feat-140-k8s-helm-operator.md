## feat(k8s): Helm chart for Shomer operator deployment

## Summary

Production-ready Helm chart for deploying the Shomer Kubernetes operator: deployment, RBAC, CRD installation, configuration, and monitoring.

## Changes

- [ ] Helm chart structure (Chart.yaml, values.yaml, templates/)
- [ ] Operator Deployment with configurable replicas, resources, image
- [ ] ServiceAccount, ClusterRole, ClusterRoleBinding
- [ ] CRD installation via Helm hooks or crds/ directory
- [ ] ConfigMap/Secret for operator configuration (API URL, auth)
- [ ] Optional ServiceMonitor for Prometheus metrics
- [ ] values.yaml with sensible defaults
- [ ] Helm chart tests
- [ ] README with installation instructions

## Dependencies

- #134 - operator scaffold

## Related Issue

Closes #140

## Test Plan

- [ ] `make format` - code formatted
- [ ] `make lint` - no linting errors
- [ ] `make typecheck` - type checks pass
- [ ] `make test` - all unit tests pass
- [ ] `make bdd` - all BDD tests pass
- [ ] `make check-license` - SPDX headers present


