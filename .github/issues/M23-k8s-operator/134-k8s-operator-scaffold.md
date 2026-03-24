# feat(k8s): Kubernetes operator scaffold with controller-runtime

## Description

Scaffold the Shomer Kubernetes operator using kubebuilder and controller-runtime (Go). Set up the project structure, CRD generation, RBAC, leader election, and Helm chart for deploying the operator.

## Objective

Establish the operator foundation that all custom resource controllers will build upon.

## Tasks

- [ ] kubebuilder project initialization
- [ ] Operator configuration: Shomer API URL, authentication (PAT secret reference or ServiceAccount-based)
- [ ] HTTP client for Shomer admin API with retry and error handling
- [ ] Leader election for HA deployments
- [ ] RBAC (ClusterRole, ServiceAccount) for the operator
- [ ] Helm chart for operator deployment
- [ ] CI: build, lint, test, Docker image, Helm publish
- [ ] Integration test framework (envtest)

## Dependencies

None — this is the operator foundation.

## Labels

`type:infra`, `size:L`
