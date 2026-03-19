# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>


.PHONY: help env install format lint typecheck test bdd docker-build docker-up docker-down kind-up kind-down kind-bdd migrate migrate-auto license check-license release pytest-report behave-report docs serve-docs build publish clean

VENV = .venv

help: ## Show this help
	@echo "📘 Available commands:"; \
	grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

env: ## Set up virtual environment
	@if ! test -x $(VENV)/bin/python; then \
		echo "🔧 Installing dependencies with Poetry..."; \
		poetry install --with dev --with docs --with test --extras server --extras worker; \
	fi

install: env ## Install dependencies with Poetry
	@echo "📦 Dependencies installed and ready."

format: env ## Format code with isort and ruff format
	@echo "🎨 Formatting code with isort and ruff..."
	@poetry run isort .
	@poetry run ruff format

lint: env ## Lint code with Ruff
	@echo "🔍 Linting code with Ruff..."
	@poetry run ruff check --fix .

typecheck: env ## Run MyPy type checks
	@echo "🔎 Type checking with MyPy..."
	@poetry run mypy src/ tests/

test: env ## Run tests with pytest and coverage
	@echo "🧪 Running tests with pytest..."
	poetry run pytest

bdd: env ## Run BDD tests with behave and playwright
	@echo "🎭 Running BDD tests with behave..."
	poetry run behave

docker-build: ## Build the Docker image
	@echo "🐳 Building Docker image..."
	@docker compose build

docker-up: ## Start the app via Docker Compose
	@echo "🐳 Starting app..."
	@docker compose up -d --build --wait
	@echo "✅ App running at http://localhost:8000"

docker-down: ## Stop the app via Docker Compose
	@echo "🐳 Stopping app..."
	@docker compose down

kind-up: ## Deploy to a local kind cluster with ingress
	@echo "☸️ Creating kind cluster..."
	@kind create cluster --name shomer --config kind-config.yaml 2>/dev/null || true
	@echo "☸️ Installing ingress-nginx..."
	@kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
	@echo "☸️ Waiting for ingress controller..."
	@kubectl wait --namespace ingress-nginx \
		--for=condition=ready pod \
		--selector=app.kubernetes.io/component=controller \
		--timeout=120s
	@echo "🐳 Building images..."
	@docker build -f Dockerfile.server -t shomer-server:dev .
	@docker build -f Dockerfile.worker -t shomer-worker:dev .
	@echo "📦 Loading images into kind..."
	@docker save shomer-server:dev | kind load image-archive /dev/stdin --name shomer
	@docker save shomer-worker:dev | kind load image-archive /dev/stdin --name shomer
	@echo "🔧 Installing Helm chart..."
	@helm install shomer chart/shomer \
		--set image.repository=shomer-server \
		--set image.tag=dev \
		--set image.pullPolicy=Never \
		--set worker.image.repository=shomer-worker \
		--set worker.image.tag=dev \
		--set worker.image.pullPolicy=Never \
		--set beat.image.repository=shomer-worker \
		--set beat.image.tag=dev \
		--set beat.image.pullPolicy=Never \
		--set env.SHOMER_BEAT_PING_INTERVAL="10" \
		--set ingress.enabled=true \
		--set ingress.className=nginx \
		--set ingress.hosts[0].host=shomer.localhost \
		--set ingress.hosts[0].paths[0].path=/ \
		--set ingress.hosts[0].paths[0].pathType=Prefix \
		--set mailcatcher.enabled=true \
		--wait --timeout 300s
	@echo "✅ Cluster ready at http://shomer.localhost"
	@echo "   Run 'make kind-bdd' to test"

kind-down: ## Delete the local kind cluster
	@echo "☸️ Deleting kind cluster..."
	@helm uninstall shomer --ignore-not-found 2>/dev/null || true
	@kind delete cluster --name shomer

kind-bdd: env ## Run BDD tests against kind cluster
	@echo "🥒 Running BDD tests against kind..."
	@kubectl port-forward svc/shomer-mailcatcher 1080:1080 &>/dev/null &
	@kubectl port-forward svc/shomer-postgres 5432:5432 &>/dev/null &
	@sleep 3
	@BASE_URL=http://shomer.localhost MAILCATCHER_URL=http://localhost:1080 poetry run behave; \
		EXIT=$$?; \
		kill %1 %2 2>/dev/null || true; \
		exit $$EXIT

migrate: env ## Run database migrations
	@echo "🗄️ Running database migrations..."
	@poetry run alembic upgrade head

migrate-auto: env ## Auto-generate a new migration
	@echo "🗄️ Auto-generating migration..."
	@poetry run alembic revision --autogenerate -m "$(msg)"

pytest-report: env ## Generate pytest report for documentation
	@echo "📊 Generating pytest report..."
	@poetry run python scripts/generate_pytest_report.py

behave-report: env ## Generate BDD report for documentation
	@echo "📊 Generating BDD report..."
	@poetry run python scripts/generate_behave_report.py

license: env ## Add SPDX license headers to source files
	@echo "🔐 Adding license headers to source files..."
	@./scripts/add_license_header.py --path src --types py
	@./scripts/add_license_header.py --path tests --types py

check-license: env ## Check that all files have license headers
	@echo "🔍 Checking SPDX license headers..."
	@./scripts/add_license_header.py --path src --types py --check
	@./scripts/add_license_header.py --path tests --types py --check

release: env ## Bump version, update changelog and push tag
	@echo "🚀 Creating release with Commitizen..."
	@poetry run cz bump --yes --changelog

docs: env ## Build documentation using MkDocs
	@echo "📚 Building MkDocs documentation..."
	@poetry run mkdocs build

serve-docs: env ## Serve documentation locally with MkDocs
	@echo "🌐 Serving MkDocs documentation at http://127.0.0.1:8000 ..."
	@poetry run mkdocs serve

build: env ## Build the Python package (wheel and sdist)
	@echo "🏗️ Building Python package..."
	@poetry build

publish: build ## Publish the package to PyPI (requires PYPI_TOKEN)
	@if [ -z "$(PYPI_TOKEN)" ]; then \
		echo "❌ PYPI_TOKEN is not set. \nUse: export PYPI_TOKEN=your-token"; \
		exit 1; \
	fi
	@echo "📤 Publishing package to PyPI..."
	@poetry publish --username __token__ --password $(PYPI_TOKEN)

clean: ## Clean cache and build files
	@echo "🧹 Cleaning build, cache and virtualenv files..."
	@rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage coverage.xml junit.xml htmlcov site dist screenshots $(VENV)
	@find . -type d -name "__pycache__" -exec rm -rf {} +
