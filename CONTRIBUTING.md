# Contributing

Thanks for your interest in contributing to **shomer**!

## Prerequisites

- Python >= 3.10
- [Poetry](https://python-poetry.org/) >= 2.0
- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/), [helm](https://helm.sh/), [kubectl](https://kubernetes.io/docs/tasks/tools/) - optional, required to test Helm chart changes

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:

```bash
git clone https://github.com/<your-username>/shomer.git
cd shomer
```

3. **Install** dependencies:

```bash
make install
```

## Available commands

```console
make help            # Show all available commands
make install         # Install dependencies with Poetry
make format          # Format code with isort and ruff
make lint            # Lint code with Ruff
make typecheck       # Run MyPy type checks
make test            # Run tests with pytest and coverage
make bdd             # Run BDD tests with behave and playwright
make docker-build    # Build the Docker image
make docker-up       # Start the app via Docker Compose
make docker-down     # Stop the app via Docker Compose
make kind-up         # Deploy to a local kind cluster with ingress
make kind-down       # Delete the local kind cluster
make kind-bdd        # Run BDD tests against kind cluster
make migrate         # Run database migrations
make migrate-auto    # Auto-generate a new migration
make license         # Add SPDX license headers to source files
make check-license   # Check that all files have license headers
make pytest-report   # Generate pytest report for documentation
make behave-report   # Generate BDD report for documentation
make docs            # Build documentation using MkDocs
make serve-docs      # Serve documentation locally
make build           # Build the Python package
make publish         # Publish the package to PyPI
make clean           # Clean cache and build files
```

## Branch Naming

Create a branch from `main` using one of the following prefixes:

| Prefix | Usage | Example |
|---|---|---|
| `feat/` | New feature | `feat/add-token-introspection` |
| `fix/` | Bug fix | `fix/jwt-validation-error` |
| `docs/` | Documentation | `docs/update-api-reference` |
| `refactor/` | Code refactoring | `refactor/simplify-auth-flow` |
| `test/` | Adding or updating tests | `test/add-oidc-tests` |
| `chore/` | Maintenance tasks | `chore/update-dependencies` |

```bash
git checkout -b feat/my-feature
```

## Commits

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must follow this format:

```
<type>(<optional scope>): <description>
```

Use commitizen for an interactive prompt:

```bash
cz commit
```

Or write the commit manually:

```bash
git commit -m "feat: add OIDC discovery endpoint"
git commit -m "fix(token): handle expired refresh tokens"
git commit -m "docs: add usage examples to README"
```

Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

## Code Quality

Before pushing, make sure your code passes all checks:

```console
make format       # Format code
make lint         # Lint with Ruff
make typecheck    # Type check with MyPy
make test         # Run tests with pytest
make bdd          # Run BDD tests with behave and playwright
make check-license # Verify SPDX license headers
```

All source files must include an SPDX license header. Add them automatically with:

```bash
make license
```

## Testing the Helm chart

If you modify the Helm chart (`chart/shomer/`), test it locally with [kind](https://kind.sigs.k8s.io/) before pushing:

```bash
make kind-up       # Create cluster, build images, deploy chart with ingress
make kind-bdd      # Run BDD tests against the cluster
make kind-down     # Delete the cluster
```

This deploys the full stack (server, worker, beat, postgres, redis, ingress-nginx) and runs the same BDD tests used in CI.

Prerequisites: [kind](https://kind.sigs.k8s.io/), [helm](https://helm.sh/), [kubectl](https://kubernetes.io/docs/tasks/tools/).

## Pull Request

1. Push your branch to your fork:

```bash
git push origin feat/my-feature
```

2. Open a **Pull Request** against the `main` branch

3. In your PR description:
   - Describe **what** the PR does and **why**
   - Reference related issues (e.g. `Closes #42`)
   - Include steps to test or verify the changes

4. Make sure CI passes (Lint, Type Check, Unit Tests)

5. Wait for review and address feedback if needed

