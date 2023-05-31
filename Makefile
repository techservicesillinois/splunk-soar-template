# DO NOT EDIT - All project-specific values belong in config.mk!

.PHONY: all build clean lint static
include config.mk

MODULE:=app
TEST_APP_NAME:=Test $(PROD_APP_NAME)

PACKAGE:=app
SRCS_DIR:=src/$(MODULE)
TSCS_DIR:=tests
SOAR_SRCS:=$(shell find $(SRCS_DIR) -type f)
SRCS:=$(shell find $(SRCS_DIR) -name '*.py')
TSCS:=$(shell find $(TSCS_DIR) -name '*.py')
VERSIONED_FILES:=$(addprefix $(SRCS_DIR)/, $(PACKAGE).json *.py)
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
build: .appjson $(PACKAGE).tar

build-test: export APP_ID=$(TEST_APP_ID)
build-test: export APP_NAME=$(TEST_APP_NAME)
build-test: .appjson $(PACKAGE).tar

$(PACKAGE).tar: version $(SOAR_SRCS)
	-find src -type d -name __pycache__ -exec rm -fr "{}" \;
	tar cvf $@ -C src $(MODULE)

version: .tag .commit .deployed
.tag: $(VERSIONED_FILES)
	echo version $(TAG)
	sed $(SED_INPLACE) "s/GITHUB_TAG/$(TAG)/" $^
	touch $@
.commit: $(VERSIONED_FILES)
	echo commit $(GITHUB_SHA)
	sed $(SED_INPLACE) "s/GITHUB_SHA/$(GITHUB_SHA)/" $^
	touch $@
.deployed: $(VERSIONED_FILES)
	echo deployed $(BUILD_TIME)
	sed $(SED_INPLACE) "s/BUILD_TIME/$(BUILD_TIME)/" $^
	touch $@
.appjson: $(SRCS_DIR)/$(PACKAGE).json
	echo appid: $(APP_ID)
	echo name:  $(APP_NAME)
	sed $(SED_INPLACE) "s/APP_ID/$(APP_ID)/" $^
	sed $(SED_INPLACE) "s/APP_NAME/$(APP_NAME)/" $^
	sed $(SED_INPLACE) "s/MODULE/$(MODULE)/" $^
	touch $@

deploy: $(PACKAGE).tar
	phantom deploy --file $^

venv: requirements-test.txt
	rm -rf $@
	python -m venv venv
	$(VENV_PYTHON) -m pip install -r $^

requirements-test.txt: export PYTEST_SOAR_REPO=git+https://github.com/splunk/pytest-splunk-soar-connectors.git
requirements-test.txt: requirements-test.in
	rm -rf $(VENV_REQS)
	python -m venv $(VENV_REQS)
	$(VENV_REQS)/bin/python -m pip install -r $^
	$(VENV_REQS)/bin/python -m pip freeze -qqq > $@
# REMOVE once pytest-splunk-soar-connectors is on pypi
	sed $(SED_INPLACE) "s;^pytest-splunk-soar-connectors==.*;$(PYTEST_SOAR_REPO);" $@

lint: venv .lint
.lint: $(SRCS) $(TSCS)
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

test: lint static unit
	
clean:
	rm -rf venv $(VENV_REQS)
	rm -rf .lint .static
	rm -rf .mypy_cache
	rm -f $(PACKAGE).tar .tag
	-find src -type d -name __pycache__ -exec rm -fr "{}" \;
	git checkout -- $(TAG_FILES)

force-clean: clean
	rm -f requirements-test.txt
