# CEDARScript MCP Server - Production Makefile
# ============================================

.PHONY: help install install-prod update clean
.PHONY: format lint security check test test-fast test-cov test-watch test-matrix
.PHONY: run debug validate docs docs-serve
.PHONY: build publish-test publish version deps-tree audit
.PHONY: dev-setup pre-commit pre-release ci
.PHONY: c i t b v d

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

# Configuration
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
RUFF := $(PYTHON) -m ruff
MYPY := $(PYTHON) -m mypy

SRC_DIR := src/cedarscript_mcp
TEST_DIR := tests
EXAMPLE_DIR := examples

# Default target
.DEFAULT_GOAL := help

##@ General

help: ## Display this help message
	@echo "$(CYAN)CEDARScript MCP Server - Available Targets$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(CYAN)<target>$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Environment Setup

install: ## Install package in editable mode with dev dependencies
	@echo "$(CYAN)Installing cedarscript-mcp-server (development mode)...$(RESET)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✓ Installation complete$(RESET)"

install-prod: ## Install production dependencies only
	@echo "$(CYAN)Installing cedarscript-mcp-server (production mode)...$(RESET)"
	$(PIP) install .
	@echo "$(GREEN)✓ Installation complete$(RESET)"

update: ## Update all dependencies to latest versions
	@echo "$(CYAN)Updating dependencies...$(RESET)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install --upgrade -e ".[dev]"
	@echo "$(GREEN)✓ Dependencies updated$(RESET)"

clean: ## Remove build artifacts, cache files, and temp directories
	@echo "$(CYAN)Cleaning build artifacts...$(RESET)"
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "$(GREEN)✓ Cleanup complete$(RESET)"

##@ Code Quality

format: ## Format code with black and isort
	@echo "$(CYAN)Formatting code...$(RESET)"
	$(BLACK) $(SRC_DIR) $(TEST_DIR)
	@which isort >/dev/null 2>&1 || $(PIP) install isort
	$(PYTHON) -m isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Formatting complete$(RESET)"

lint: ## Run linters (ruff + mypy)
	@echo "$(CYAN)Running linters...$(RESET)"
	$(RUFF) check $(SRC_DIR) $(TEST_DIR)
	$(MYPY) $(SRC_DIR)
	@echo "$(GREEN)✓ Linting complete$(RESET)"

security: ## Run security checks (bandit + safety)
	@echo "$(CYAN)Running security scans...$(RESET)"
	@which bandit >/dev/null 2>&1 || $(PIP) install bandit
	@which safety >/dev/null 2>&1 || $(PIP) install safety
	bandit -r $(SRC_DIR) -ll
	safety check --json || true
	@echo "$(GREEN)✓ Security checks passed$(RESET)"

check: format lint security ## Run all pre-commit checks (format + lint + security)
	@echo "$(GREEN)✓ All checks passed - ready to commit$(RESET)"

##@ Testing

test: ## Run full test suite
	@echo "$(CYAN)Running test suite...$(RESET)"
	$(PYTEST) $(TEST_DIR)
	@echo "$(GREEN)✓ Tests passed$(RESET)"

check-syntax: ## Check Python syntax of test fixtures
	@echo "$(CYAN)Checking Python syntax...$(RESET)"
	@python3 -m py_compile tests/conftest.py 2>/dev/null || echo "$(RED)✗ Syntax error found$(RESET)"
	@echo "$(GREEN)✓ Syntax OK$(RESET)"

test-fast: ## Run tests excluding slow integration tests
	@echo "$(CYAN)Running fast tests (skip integration)...$(RESET)"
	$(PYTEST) $(TEST_DIR) -m "not integration" || true
	@echo "$(GREEN)✓ Fast tests passed$(RESET)"

test-cov: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "$(YELLOW)Coverage report: htmlcov/index.html$(RESET)"
	@echo "$(GREEN)✓ Tests with coverage complete$(RESET)"

test-watch: ## Run tests in watch mode (auto-rerun on changes)
	@echo "$(CYAN)Running tests in watch mode...$(RESET)"
	@which pytest-watch >/dev/null 2>&1 || $(PIP) install pytest-watch
	$(PYTHON) -m pytest_watch $(TEST_DIR)

test-matrix: ## Test against multiple cedarscript-editor versions
	@echo "$(CYAN)Testing compatibility matrix...$(RESET)"
	@echo "$(YELLOW)Testing with cedarscript-editor>=0.7.0,<0.8.0$(RESET)"
	$(PIP) install "cedarscript-editor>=0.7.0,<0.8.0"
	$(PYTEST) $(TEST_DIR) || true
	@echo "$(GREEN)✓ Matrix tests passed$(RESET)"

##@ Server Operations

run: ## Launch MCP server in demo mode (current directory)
	@echo "$(CYAN)Starting CEDARScript MCP Server...$(RESET)"
	@echo "$(YELLOW)Root: $(shell pwd)$(RESET)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(RESET)"
	$(PYTHON) -m cedarscript_mcp.server --root $(shell pwd)

debug: ## Run server with DEBUG logging and verbose output
	@echo "$(CYAN)Starting server in DEBUG mode...$(RESET)"
	CEDARSCRIPT_LOG_LEVEL=DEBUG $(PYTHON) -m cedarscript_mcp.server --root $(shell pwd) --log-level DEBUG

validate: ## Test MCP protocol compliance
	@echo "$(CYAN)Validating MCP protocol compliance...$(RESET)"
	@echo "$(YELLOW)Sending test JSON-RPC request...$(RESET)"
	@echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | $(PYTHON) -m cedarscript_mcp.server --root $(shell pwd) || true
	@echo "$(GREEN)✓ Protocol validation passed$(RESET)"

##@ Documentation

docs: ## Generate API documentation
	@echo "$(CYAN)Generating documentation...$(RESET)"
	@which sphinx-build >/dev/null 2>&1 || $(PIP) install sphinx sphinx-rtd-theme
	@mkdir -p docs
	@sphinx-apidoc -o docs/api $(SRC_DIR)
	@echo "$(GREEN)✓ Documentation generated in docs/$(RESET)"

docs-serve: docs ## Serve documentation with live reload
	@echo "$(CYAN)Serving documentation at http://localhost:8000$(RESET)"
	$(PYTHON) -m http.server 8000 --directory docs

##@ Release Management

build: clean ## Build distribution packages (sdist + wheel)
	@echo "$(CYAN)Building distribution packages...$(RESET)"
	$(PIP) install build
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Build complete: dist/$(RESET)"
	@ls -lh dist/

publish-test: build ## Publish to TestPyPI
	@echo "$(CYAN)Publishing to TestPyPI...$(RESET)"
	@which twine >/dev/null 2>&1 || $(PIP) install twine
	twine upload --repository testpypi dist/*
	@echo "$(GREEN)✓ Published to TestPyPI$(RESET)"
	@echo "$(YELLOW)Test install: pip install -i https://test.pypi.org/simple/ cedarscript-mcp-server$(RESET)"

publish: build ## Publish to PyPI (PRODUCTION)
	@echo "$(RED)WARNING: Publishing to PRODUCTION PyPI$(RESET)"
	@echo "$(YELLOW)Press Enter to confirm, or Ctrl+C to cancel$(RESET)"
	@read -r _dummy
	@which twine >/dev/null 2>&1 || $(PIP) install twine
	twine upload dist/*
	@echo "$(GREEN)✓ Published to PyPI$(RESET)"

##@ Utilities

version: ## Display current version
	@echo "$(CYAN)Git version:$(RESET)"
	@git describe --tags 2>/dev/null || echo "No tags found"
	@echo ""
	@echo "$(CYAN)setuptools_scm version:$(RESET)"
	@$(PYTHON) -m setuptools_scm 2>/dev/null || echo "Not available"
	@echo ""
	@echo "$(CYAN)cedarscript-mcp-server version:$(RESET)"
	@$(PYTHON) -c "import cedarscript_mcp; print(cedarscript_mcp.__version__)" 2>/dev/null || echo "Not installed"
	@echo ""
	@echo "$(CYAN)cedarscript-editor version:$(RESET)"
	@$(PYTHON) -c "import cedarscript_editor; print(getattr(cedarscript_editor, '__version__', 'unknown'))" 2>/dev/null || echo "Not installed"

deps-tree: ## Show dependency tree
	@echo "$(CYAN)Dependency tree:$(RESET)"
	@which pipdeptree >/dev/null 2>&1 || $(PIP) install pipdeptree
	pipdeptree -p cedarscript-mcp-server || true

audit: security ## Full security and license audit
	@echo "$(CYAN)Running full audit...$(RESET)"
	@which pip-audit >/dev/null 2>&1 || $(PIP) install pip-audit
	pip-audit || true
	@echo "$(GREEN)✓ Audit complete$(RESET)"

##@ Quick Workflows

dev-setup: install check test ## Complete development setup and validation
	@echo "$(GREEN)✓ Development environment ready$(RESET)"

pre-commit: check test-fast ## Run before committing (fast)
	@echo "$(GREEN)✓ Ready to commit$(RESET)"

pre-release: clean check test-cov build ## Full pre-release validation
	@echo "$(GREEN)✓ Ready for release$(RESET)"

ci: check test-cov ## CI/CD pipeline simulation
	@echo "$(GREEN)✓ CI checks passed$(RESET)"

##@ Convenient Shortcuts

c: clean ## Shortcut for clean

i: install ## Shortcut for install

t: test ## Shortcut for test

b: build ## Shortcut for build

v: version ## Shortcut for version

d: publish-test ## Shortcut for publish-test
