# DO NOT EDIT - All project-specific values belong in config.mk!

.PHONY: all build build-test clean lint static python-version wheels check_template
include config.mk

MODULE:=app
TEST_APP_NAME:=Test $(PROD_APP_NAME)
SOAR_PYTHON_VERSION:=$(shell PYTHONPATH=tests python -c 'from test_python_version import SOAR_PYTHON_VERSION as V; print(f"{V[0]}.{V[1]}")')

PACKAGE:=app
SRCS_DIR:=src/$(MODULE)
TSCS_DIR:=tests
DIST_DIR:=dist/$(MODULE)
DIST_SRCS:=$(addprefix $(DIST_DIR)/, app.json app.py logo.png)
SRCS:=$(shell find $(SRCS_DIR) -name '*.py')
TSCS:=$(shell find $(TSCS_DIR) -name '*.py')
BUILD_TIME:=$(shell date -u +%FT%X.%6NZ)
VENV_PYTHON:=venv/bin/python
VENV_REQS:=.requirements.venv
UNAME:=$(shell uname -s)
WHEELS:=dist/app/wheels

ifeq (tag, $(GITHUB_REF_TYPE))
	TAG?=$(GITHUB_REF_NAME)
else
	TAG?=$(shell printf "0.0.%d" 0x$(shell git rev-parse --short=6 HEAD))
endif
GITHUB_SHA?=$(shell git rev-parse HEAD)

all: build

build: export APP_ID=$(PROD_APP_ID)
build: export APP_NAME=$(PROD_APP_NAME)
build: $(PACKAGE).tar

build-test: export APP_ID=$(TEST_APP_ID)
build-test: export APP_NAME=$(TEST_APP_NAME)
build-test: $(PACKAGE).tar


deps: deps-deploy
deps-deploy: # Install deps for deploy.py on Github
	pip install requests

dist: $(DIST_SRCS)
$(DIST_DIR):
	mkdir -p $@
$(DIST_DIR)/app.py: $(SRCS_DIR)/app.py $(DIST_DIR)
	sed "s/GITHUB_TAG/$(TAG)/;s/GITHUB_SHA/$(GITHUB_SHA)/;s/BUILD_TIME/$(BUILD_TIME)/" $< > $@
$(DIST_DIR)/logo.png: $(SRCS_DIR)/logo.png $(DIST_DIR) 
	cp -r $< $(DIST_DIR)
$(DIST_DIR)/app.json: $(SRCS_DIR)/app.json $(DIST_DIR) venv wheels
    # LC_ALL=C is needed on macOS to avoid illegal byte sequence error
	LC_ALL=C sed "s/APP_ID/$(APP_ID)/;s/APP_NAME/$(APP_NAME)/;s/MODULE/$(MODULE)/" $< |\
	$(VENV_PYTHON) -m phtoolbox deps -o $@ $(DIST_DIR)/wheels

$(PACKAGE).tar: $(DIST_SRCS)
	tar cvf $@ -C dist $(MODULE)

deploy: $(PACKAGE).tar venv
	$(VENV_PYTHON) -m phtoolbox deploy --file $<

python-version:
	@echo $(SOAR_PYTHON_VERSION)

.python-version: tests/test_python_version.py
	pyenv install -s $(SOAR_PYTHON_VERSION)
	pyenv local $(SOAR_PYTHON_VERSION)

venv: requirements-test.txt .python-version
	rm -rf $@
	python -m venv venv
	$(VENV_PYTHON) -m pip install -r $<

wheels: $(DIST_DIR) $(WHEELS)
$(WHEELS): requirements.in
	pip wheel --no-deps --wheel-dir=$@ -r $^

requirements-test.txt: export PYTEST_SOAR_REPO=git+https://github.com/splunk/pytest-splunk-soar-connectors.git
requirements-test.txt: requirements-test.in
	rm -rf $(VENV_REQS)
	python -m venv $(VENV_REQS)
	$(VENV_REQS)/bin/python -m pip install -r $^
	$(VENV_REQS)/bin/python -m pip freeze -qqq | \
	sed "s;^pytest-splunk-soar-connectors==.*;$(PYTEST_SOAR_REPO);" >  $@
# REMOVE sed line above once pytest-splunk-soar-connectors is on pypi

lint: venv .lint
.lint: $(SRCS) $(TSCS) soar_template
	$(VENV_PYTHON) -m flake8 $?
	touch $@

static: venv .static
.static: $(SRCS) $(TSCS)
	echo "Code: $(SRCS)"
	echo "Test: $(TSCS)"
	$(VENV_PYTHON) -m mypy $^
	touch $@

unit: venv
	$(VENV_PYTHON) -m pytest

autopep8:
	autopep8 --in-place $(SRCS)

check_template: venv .check_template
.check_template: Makefile soar_template .github/workflows/deploy.yml tests/test_python_version.py
	$(VENV_PYTHON) soar_template compare

test: lint static check_template unit 

clean:
	rm -rf venv $(VENV_REQS)
	rm -rf .lint .static
	rm -rf .mypy_cache
	rm -rf dist
	rm -f $(PACKAGE).tar .tag

force-clean: clean
	rm -f requirements-test.txt .python-version
