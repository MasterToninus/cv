# Python owns the build on every platform. Override with make PYTHON=python.
PYTHON ?= python3
.DEFAULT_GOAL := all
DATE_ARG = $(if $(DATE),--date $(DATE),)
FORMAT ?= all
FORMAT_ARG = --format $(FORMAT)
PYTHON_SOURCES = build.py generate.py getactivities.py cvgen tests

.PHONY: all tex clean refresh-activities check test format format-check

all:
	$(PYTHON) build.py $(DATE_ARG) $(FORMAT_ARG)

tex:
	$(PYTHON) build.py --tex-only $(DATE_ARG) $(FORMAT_ARG)

clean:
	$(PYTHON) build.py --clean

refresh-activities:
	$(PYTHON) build.py --refresh-activities

check:
	$(PYTHON) build.py --check-tools $(FORMAT_ARG)

test:
	$(PYTHON) -m unittest discover -s tests -v

format:
	$(PYTHON) -m isort $(PYTHON_SOURCES)
	$(PYTHON) -m black $(PYTHON_SOURCES)

format-check:
	$(PYTHON) -m isort --check-only $(PYTHON_SOURCES)
	$(PYTHON) -m black --check $(PYTHON_SOURCES)
