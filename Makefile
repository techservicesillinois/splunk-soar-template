# DO NOT EDIT - All project-specific values belong in config.mk!

.PHONY: all build build-test clean lint static python-version wheels
include config.mk

MODULE:=app
TEST_APP_NAME:=Test $(PROD_APP_NAME)
SOAR_PYTHON_VERSION:=$(shell PYTHONPATH=tests python -c 'from test_python_version import SOAR_PYTHON_VERSION as V; print(f"{V[0]}.{V[1]}")')

PACKAGE:=app
SRCS_DIR:=src/$(MODULE)
TSCS_DIR:=tests
SOAR_SRCS:=$(shell find $(SRCS_DIR) -type f)
DIST_DIR:=dist/$(MODULE)
DIST_SRCS:=$(addprefix $(DIST_DIR)/, $(PACKAGE).json *.py)
SRCS:=$(shell find $(SRCS_DIR) -name '*.py')
TSCS:=$(shell find $(TSCS_DIR) -name '*.py')
BUILD_TIME:=$(shell date -u +%FT%X.%6NZ)
VENV_PYTHON:=venv/bin/python
VENV_REQS:=.requirements.venv
UNAME:=$(shell uname -s)

# BSD `sed` treats the `-i` option differently than Linux and others.
# Check for Mac OS X 'Darwin' and set our `-i` option accordingly.
ifeq ($(UNAME), Darwin)
# macOS (BSD sed)
	SED_INPLACE := -i ''
else
# Linux and others (GNU sed)
	SED_INPLACE := -i
endif

ifeq (tag, $(GITHUB_REF_TYPE))
	TAG?=$(GITHUB_REF_NAME)
else
	TAG?=$(shell printf "0.0.%d" 0x$(shell git rev-parse --short=6 HEAD))
endif
GITHUB_SHA?=$(shell git rev-parse HEAD)

all: build

build: export APP_ID=$(PROD_APP_ID)
build: export APP_NAME=$(PROD_APP_NAME)
build: dist $(PACKAGE).tar

build-test: export APP_ID=$(TEST_APP_ID)
build-test: export APP_NAME=$(TEST_APP_NAME)
build-test: dist $(PACKAGE).tar


deps: deps-deploy
deps-deploy: # Install deps for deploy.py on Github
	pip install requests

dist: $(DIST_DIR) $(DIST_SRCS) .appjson version
$(DIST_DIR):
	mkdir -p $@
$(DIST_SRCS): $(SOAR_SRCS)
	cp -r $^ $(DIST_DIR)

$(PACKAGE).tar: version $(SOAR_SRCS) wheels
	-find src -type d -name __pycache__ -exec rm -fr "{}" \;
	tar cvf $@ -C src $(MODULE)

version: .tag .commit .deployed
.tag: $(DIST_SRCS)
	echo version $(TAG)
	sed $(SED_INPLACE) "s/GITHUB_TAG/$(TAG)/" $^
	touch $@
.commit: $(DIST_SRCS)
	echo commit $(GITHUB_SHA)
	sed $(SED_INPLACE) "s/GITHUB_SHA/$(GITHUB_SHA)/" $^
	touch $@
.deployed: $(DIST_SRCS)
	echo deployed $(BUILD_TIME)
	sed $(SED_INPLACE) "s/BUILD_TIME/$(BUILD_TIME)/" $^
	touch $@
.appjson: $(DIST_DIR)/$(PACKAGE).json $(WHEELS)
	echo appid: $(APP_ID)
	echo name:  $(APP_NAME)
	echo wheel: $(shell ls $(WHEELS))
	sed $(SED_INPLACE) "s/APP_ID/$(APP_ID)/" $^
	sed $(SED_INPLACE) "s/APP_NAME/$(APP_NAME)/" $^
	sed $(SED_INPLACE) "s/MODULE/$(MODULE)/" $^
	@echo "WHEELS: $(WHEELS)"
# TODO: Add a SED command here for any custom library packaging.
# sed $(SED_INPLACE) "s/WHEEL_TDX/$(shell ls $(WHEELS) | grep -E 'TDX.*\.whl')/" $@
	sed $(SED_INPLACE) "s/WHEEL_TOOLBOX/$(shell ls ./$(WHEELS) | grep -E 'phantom_toolbox.*\.whl')/" $@
	touch $@

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

wheels: $(WHEELS)
$(WHEELS): requirements.in
	pip wheel --no-deps --wheel-dir=$@ -r $^

requirements-test.txt: export PYTEST_SOAR_REPO=git+https://github.com/splunk/pytest-splunk-soar-connectors.git
requirements-test.txt: requirements-test.in
	rm -rf $(VENV_REQS)
	python -m venv $(VENV_REQS)
	$(VENV_REQS)/bin/python -m pip install -r $^
	$(VENV_REQS)/bin/python -m pip freeze -qqq > $@
# REMOVE once pytest-splunk-soar-connectors is on pypi
	sed $(SED_INPLACE) "s;^pytest-splunk-soar-connectors==.*;$(PYTEST_SOAR_REPO);" $@

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
.check_template:
	$(VENV_PYTHON) soar_template compare
	touch $@

test: lint static check_template unit 

clean:
	rm -rf venv $(VENV_REQS)
	rm -rf .lint .static
	rm -rf .mypy_cache
	rm -rf dist
	rm -f $(PACKAGE).tar .tag

force-clean: clean
	rm -f requirements-test.txt .python-version
