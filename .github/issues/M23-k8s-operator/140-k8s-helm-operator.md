# feat(k8s): Helm chart for Shomer operator deployment

## Description

Production-ready Helm chart for deploying the Shomer Kubernetes operator: deployment, RBAC, CRD installation, configuration, and monitoring.

## Objective

Provide a one-command deployment of the operator into any Kubernetes cluster.

## Tasks

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

- #134 — operator scaffold

## Labels

`type:infra`, `size:M`
