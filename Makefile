.PHONY: help setup dev test lint fmt analyze clean install

# Default target
help: ## Show this help message
	@echo "Ascent Planner Calendar Application"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup
setup: ## Install dependencies and setup environment
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt

install: ## Install package in development mode
	python3 -m pip install -e .

##@ Development
dev: ## Run development server (Streamlit)
	python3 -m streamlit run src/app/planner_app.py --server.port 8501

api: ## Run API server (FastAPI)
	cd /Users/jeffjackson/Desktop/Planner && python3 -c "import uvicorn; from src.app.web import app; uvicorn.run(app, host='0.0.0.0', port=8000)"

analyze: ## Analyze Excel spreadsheet structure
	python3 analyze_excel.py

##@ Testing & Quality
test: ## Run tests (placeholder)
	@echo "Tests not implemented yet"

lint: ## Run linting (placeholder)
	@echo "Linting not implemented yet"

fmt: ## Format code (placeholder)
	@echo "Formatting not implemented yet"

##@ Cleanup
clean: ## Clean up temporary files
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ .coverage .pytest_cache/
