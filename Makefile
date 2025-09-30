# DO NOT EDIT - All project-specific values belong in config.mk!

.PHONY: all autopep8 build build-test clean lint static python-version wheels check_template
include config.mk

TEST_APP_NAME:=Test $(PROD_APP_NAME)
SOAR_PYTHON_VERSION:=$(shell PYTHONPATH=tests python -c 'from test_python_version import SOAR_PYTHON_VERSION as V; print(f"{V[0]}.{V[1]}")')

ifeq (src/app/readme.html, $(wildcard src/app/readme.html))
	DIST_OPT:=readme.html
endif

DIST_SRCS:=$(addprefix dist/app/, app.json app.py app.png $(DIST_OPT))
SRCS:=$(shell find src/app -name '*.py')
TSCS:=$(shell find tests -name '*.py')
BUILD_TIME:=$(shell date -u +%FT%X.%6NZ)
VENV_PYTHON:=venv/bin/python
VENV_REQS:=.requirements.venv
UNAME:=$(shell uname -s)

ifeq (tag, $(GITHUB_REF_TYPE))
	TAG?=$(GITHUB_REF_NAME)
else
	TAG?=$(shell printf "0.0.%d" 0x$(shell git rev-parse --short=6 HEAD))
endif
GITHUB_SHA?=$(shell git rev-parse HEAD)

all: build

build: export APP_ID=$(PROD_APP_ID)
build: export APP_NAME=$(PROD_APP_NAME)
build: app.tar

build-test: export APP_ID=$(TEST_APP_ID)
build-test: export APP_NAME=$(TEST_APP_NAME)
build-test: app.tar


deps: deps-deploy
deps-deploy: # Install deps for deploy.py on Github
	pip install requests

dist: $(DIST_SRCS)
dist/app:
	mkdir -p $@
dist/app/app.py: src/app/app.py dist/app
	sed "s/GITHUB_TAG/$(TAG)/;s/GITHUB_SHA/$(GITHUB_SHA)/;s/BUILD_TIME/$(BUILD_TIME)/" $< > $@
dist/app/app.json: src/app/app.json dist/app venv wheels
    # LC_ALL=C is needed on macOS to avoid illegal byte sequence error
	LC_ALL=C sed "s/APP_ID/$(APP_ID)/;s/APP_NAME/$(APP_NAME)/;s/GITHUB_TAG/$(TAG)/;s/BUILD_TIME/$(BUILD_TIME)/" $< |\
	$(VENV_PYTHON) -m phtoolbox deps -o $@ dist/app/wheels
dist/app/%: src/app/% dist/app
	cp -r $< $@

app.tar: $(DIST_SRCS)
	tar cvf $@ -C dist app

deploy: app.tar venv
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

wheels: dist/app dist/app/wheels
dist/app/wheels: requirements.in
	pip wheel --no-deps --wheel-dir=$@ -r $^

requirements-test.txt: export PYTEST_SOAR_REPO=git+https://github.com/splunk/pytest-splunk-soar-connectors.git
requirements-test.txt: requirements-test.in requirements.in
	rm -rf $(VENV_REQS)
	python -m venv $(VENV_REQS)
	$(VENV_REQS)/bin/python -m pip install -r requirements.in
	$(VENV_REQS)/bin/python -m pip install -r requirements-test.in
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

autopep8: .autopep8
.autopep8: $(SRCS) $(TSCS) soar_template
	autopep8 --in-place $?
	touch $@

check_template: venv .check_template
.check_template: Makefile soar_template .github/workflows/deploy.yml tests/test_python_version.py
	$(VENV_PYTHON) soar_template compare

test: lint static check_template unit

clean:
	rm -rf venv $(VENV_REQS)
	rm -rf .lint .static
	rm -rf .mypy_cache
	rm -rf dist
	rm -f app.tar

force-clean: clean
	rm -f requirements-test.txt .python-version
