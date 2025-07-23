# Crowd Management Agentic AI - Configuration

# Project Structure
SRC_DIR="src"
TESTS_DIR="tests"
EXAMPLES_DIR="examples"

# Python Configuration
PYTHON_VERSION="3.8+"
VIRTUAL_ENV_NAME="g1"


# Development Commands
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black flake8

setup-env:
	source ~/$(VIRTUAL_ENV_NAME)/bin/activate && pip install -r requirements.txt

run:
	python3 main.py

demo:
	python examples/demo.py

test:
	python -m pytest tests/ -v

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html

format:
	black src/ tests/ examples/
	flake8 src/ tests/ examples/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker build -t crowd-management-ai .

docker-run:
	docker run -p 8000:8000 --env-file .env crowd-management-ai

help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  install-dev  - Install dev dependencies"
	@echo "  setup-env    - Create virtual environment"
	@echo "  run          - Run the main application"
	@echo "  demo         - Run the demonstration script"
	@echo "  test         - Run tests"
	@echo "  test-coverage- Run tests with coverage"
	@echo "  format       - Format code"
	@echo "  clean        - Clean temporary files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

.PHONY: install install-dev setup-env run demo test test-coverage format clean docker-build docker-run help
