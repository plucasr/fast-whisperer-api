.PHONY: venv install clean run help

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "Available commands:"
	@echo "  make venv      - Create virtual environment"
	@echo "  make install   - Install dependencies from requirements.txt"
	@echo "  make run       - Run the script"
	@echo "  make clean     - Remove virtual environment"
	@echo ""
	@echo "To activate the venv manually, run:"
	@echo "  source venv/bin/activate"

venv:
	@echo "Creating virtual environment..."
	python -m venv .venv
	@echo "Virtual environment created!"
	@echo "Run 'source venv/bin/activate' to activate it"
	source venv/bin/activate

install: venv
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install youtube-transcript-api
	@echo "Dependencies installed!"

run:
	@echo "Running script..."
	$(PYTHON) your_script.py

clean:
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Virtual environment removed!"
