.PHONY: venv install clean run help dev test-db

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "Available commands:"
	@echo "  make venv      - Create virtual environment"
	@echo "  make install   - Install dependencies from requirements.txt"
	@echo "  make run       - Run the script"
	@echo "  make test-db   - Test database connectivity"
	@echo "  make dev       - Setup venv, install dependencies, and run the server"
	@echo "  make clean     - Remove virtual environment"
	@echo ""
	@echo "To activate the venv manually, run:"
	@echo "  source $(VENV)/bin/activate"

venv:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	@echo "Virtual environment created!"
	@echo "Run 'source $(VENV)/bin/activate' to activate it"

install: venv
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Dependencies installed!"

run:
	@echo "Running server..."
	$(PYTHON) main.py

dev: install run

clean:
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Virtual environment removed!"

list-models:
	@echo "Listing available models..."
	$(PYTHON) list_models.py

test-db:
	@echo "Testing database connectivity..."
	$(PYTHON) test_db.py
