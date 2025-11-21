# CEDARScript MCP Server - Makefile Design

## Philosophy

The Makefile serves as the **single source of truth** for developer workflows. It should be:
- **Discoverable**: `make help` shows all targets with descriptions
- **Idempotent**: Safe to run repeatedly
- **Cross-platform**: Works on Linux, macOS, and Windows (via Python when needed)
- **Fast**: Parallel execution where possible
- **Informative**: Colored output, clear success/failure messages

## Target Categories

### 1. Environment Setup
### 2. Code Quality
### 3. Testing
### 4. Server Operations
### 5. Documentation
### 6. Release Management
### 7. Utilities

---

## Complete Makefile Implementation

```makefile
# CEDARScript MCP Server - Production Makefile
# ============================================

.PHONY: help install install-prod update clean
.PHONY: format lint security check test test-fast test-cov test-watch test-matrix
.PHONY: run debug validate docs docs-serve
.PHONY: build publish-test publish version deps-tree audit

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
	safety check --json
	@echo "$(GREEN)✓ Security checks passed$(RESET)"

check: format lint security ## Run all pre-commit checks (format + lint + security)
	@echo "$(GREEN)✓ All checks passed - ready to commit$(RESET)"

##@ Testing

test: ## Run full test suite
	@echo "$(CYAN)Running test suite...$(RESET)"
	$(PYTEST) $(TEST_DIR)
	@echo "$(GREEN)✓ Tests passed$(RESET)"

test-fast: ## Run tests excluding slow integration tests
	@echo "$(CYAN)Running fast tests (skip integration)...$(RESET)"
	$(PYTEST) $(TEST_DIR) -m "not integration"
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
	$(PYTEST) $(TEST_DIR)
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
	@echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | $(PYTHON) -m cedarscript_mcp.server --root $(shell pwd)
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
	@read -r
	@which twine >/dev/null 2>&1 || $(PIP) install twine
	twine upload dist/*
	@echo "$(GREEN)✓ Published to PyPI$(RESET)"

##@ Utilities

version: ## Display current version
	@echo "$(CYAN)cedarscript-mcp-server version:$(RESET)"
	@$(PYTHON) -c "import cedarscript_mcp; print(cedarscript_mcp.__version__)"
	@echo ""
	@echo "$(CYAN)cedarscript-editor version:$(RESET)"
	@$(PYTHON) -c "import cedarscript_editor; print(getattr(cedarscript_editor, '__version__', 'unknown'))"

deps-tree: ## Show dependency tree
	@echo "$(CYAN)Dependency tree:$(RESET)"
	@which pipdeptree >/dev/null 2>&1 || $(PIP) install pipdeptree
	pipdeptree -p cedarscript-mcp-server

audit: security ## Full security and license audit
	@echo "$(CYAN)Running full audit...$(RESET)"
	@which pip-audit >/dev/null 2>&1 || $(PIP) install pip-audit
	pip-audit
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
```

---

## Target Descriptions

### Environment Setup

**`make install`**
- Installs package in editable mode (`pip install -e ".[dev]"`)
- Includes all development dependencies
- Fast incremental development (no reinstall needed)

**`make install-prod`**
- Production-only install (no dev deps)
- For deployment/containers
- Minimal footprint

**`make update`**
- Updates all dependencies to latest compatible versions
- Upgrades pip/setuptools first
- Useful after dependency changes

**`make clean`**
- Removes build artifacts (`dist/`, `*.egg-info`)
- Clears test/coverage caches
- Deletes `__pycache__` and `.pyc` files
- Idempotent (safe to run repeatedly)

### Code Quality

**`make format`**
- Black: Code formatting (100 char line length)
- isort: Import sorting
- Modifies files in-place

**`make lint`**
- Ruff: Fast Python linter (replaces flake8/pylint)
- mypy: Static type checking
- Fails on errors (non-zero exit)

**`make security`**
- Bandit: Security issue scanner (AST analysis)
- Safety: Vulnerability database check
- Auto-installs tools if missing

**`make check`**
- Runs `format + lint + security`
- Use before commits
- One-command validation

### Testing

**`make test`**
- Runs full pytest suite
- Includes integration tests
- Generates terminal output

**`make test-fast`**
- Skips slow integration tests (`-m "not integration"`)
- For rapid iteration
- 10x faster than full suite

**`make test-cov`**
- Runs tests with coverage tracking
- Generates HTML report (`htmlcov/`)
- Terminal summary included
- Requires 80%+ coverage (enforced in CI)

**`make test-watch`**
- Auto-reruns tests on file changes
- Uses pytest-watch
- Great for TDD workflows

**`make test-matrix`**
- Tests against multiple `cedarscript-editor` versions
- Validates compatibility claims
- Essential before releases

### Server Operations

**`make run`**
- Launches MCP server on current directory
- STDIO mode (for testing with pipes)
- Ctrl+C to stop

**`make debug`**
- Sets `CEDARSCRIPT_LOG_LEVEL=DEBUG`
- Verbose request/response logging
- Use for troubleshooting

**`make validate`**
- Sends test JSON-RPC request to server
- Validates protocol compliance
- Quick sanity check

### Documentation

**`make docs`**
- Generates Sphinx API docs
- Auto-discovers modules via sphinx-apidoc
- Output: `docs/api/`

**`make docs-serve`**
- Serves docs on `localhost:8000`
- Live preview during writing
- Auto-refreshes on rebuild

### Release Management

**`make build`**
- Cleans artifacts first
- Builds sdist + wheel (`python -m build`)
- Verifies package contents
- Lists files with sizes

**`make publish-test`**
- Uploads to TestPyPI
- Safe dry-run before production
- Provides test install command

**`make publish`**
- Uploads to production PyPI
- **Requires confirmation** (interactive prompt)
- Irreversible (use with caution)

### Utilities

**`make version`**
- Shows `cedarscript-mcp-server` version
- Shows `cedarscript-editor` version
- Quick dependency check

**`make deps-tree`**
- Visualizes dependency graph
- Uses pipdeptree
- Helps debug conflicts

**`make audit`**
- Full security audit (bandit + safety + pip-audit)
- License compliance check
- Pre-release requirement

### Quick Workflows

**`make dev-setup`**
- One-command setup: `install + check + test`
- For new developers
- Validates environment

**`make pre-commit`**
- Fast validation: `check + test-fast`
- 30-second check before commits
- Recommended git hook

**`make pre-release`**
- Complete validation: `clean + check + test-cov + build`
- Before tagging releases
- Ensures quality

**`make ci`**
- Simulates CI/CD pipeline
- Runs same checks as GitHub Actions
- Local validation before push

---

## Usage Examples

### Daily Development Workflow
```bash
# Start of day
make install

# During development
make format         # Before commits
make test-fast      # Quick validation
make pre-commit     # Before pushing

# End of day
make check test-cov # Full validation
```

### Release Workflow
```bash
# Pre-release validation
make pre-release

# Test on TestPyPI
make publish-test

# Production release
make publish
```

### Debugging Workflow
```bash
# Run server with debug logging
make debug

# Validate protocol
make validate

# Check dependencies
make deps-tree
```

### CI/CD Workflow
```bash
# Simulate CI pipeline
make ci

# Full test matrix
make test-matrix

# Security audit
make audit
```

---

## Makefile Best Practices Applied

1. **PHONY Targets**: All targets are `.PHONY` (no file conflicts)
2. **Colors**: Consistent use of ANSI colors for readability
3. **Checks**: Auto-install missing tools (`which || pip install`)
4. **Idempotency**: Safe to run repeatedly
5. **Error Handling**: Non-zero exit on failures
6. **Parallel Safety**: Targets don't conflict (can run in parallel if needed)
7. **Documentation**: Every target has `##` comment for `make help`
8. **Composability**: Targets call other targets (e.g., `check: format lint security`)

---

## Integration with CI/CD

Example GitHub Actions workflow:
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: make install
      - run: make ci  # Runs check + test-cov
```

---

**Makefile Design Version**: 1.0.0
**Last Updated**: 2025-01-21
