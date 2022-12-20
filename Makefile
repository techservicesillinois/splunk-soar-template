.PHONY: all build clean lint static
MODULE:=Illinois_midPoint
PACKAGE:=illinoismidpoint

SRCS_DIR:=src/ph$(MODULE)
TSCS_DIR:=tests
SOAR_SRCS:=$(shell find $(SRCS_DIR) -type f)
SRCS:=$(shell find $(SRCS_DIR) -name '*.py')
TSCS:=$(shell find $(TSCS_DIR) -name '*.py')
VERSION_FILES:=$(addprefix $(SRCS_DIR)/, $(PACKAGE).json app.py)
GITHUB_DEPLOYED:=$(shell date -u +%FT%X.%6NZ)
VENV_PYTHON:=venv/bin/python
VENV_REQS:=.requirements.venv

ifeq (tag, $(GITHUB_REF_TYPE))
	TAG?=$(GITHUB_REF_NAME)
else
	TAG?=0.0.0
endif
GITHUB_SHA?=$(shell git rev-parse HEAD)

all: build

build: $(PACKAGE).tgz

$(PACKAGE).tgz: version $(SOAR_SRCS)
	tar zcvf $@ -C src .

version: .tag .commit .deployed
.tag: $(VERSION_FILES)
	echo version $(TAG)
	sed -i s/GITHUB_TAG/$(TAG)/ $^
	touch $@
.commit: $(VERSION_FILES)
	echo commit $(GITHUB_SHA)
	sed -i s/GITHUB_SHA/$(GITHUB_SHA)/ $^
	touch $@
.deployed: $(VERSION_FILES)
	echo deployed $(GITHUB_DEPLOYED)
	sed -i s/GITHUB_DEPLOYED/$(GITHUB_DEPLOYED)/ $^
	touch $@

deploy: $(PACKAGE).tgz
	python deploy.py $^

venv: requirements-test.txt
	python -m venv venv
	$(VENV_PYTHON) -m pip install -r $^

requirements-test.txt: export PYTEST_SOAR_REPO=git+ssh://git@github.com/edthedev/pytest-splunk-soar-connectors.git
requirements-test.txt: requirements-test.in
	rm -rf $(VENV_REQS)
	python -m venv $(VENV_REQS)
	$(VENV_REQS)/bin/python -m pip install -r $^
	$(VENV_REQS)/bin/python -m pip freeze -qqq > $@
	#REMOVE once pytest-splunk-soar-connectors is on pypi
	sed -i "s;^pytest-splunk-soar-connectors==.*;$(PYTEST_SOAR_REPO);" $@

lint: .lint
.lint: $(SRCS) $(TSCS)
	$(VENV_PYTHON) -m flake8 $?
	touch $@

static: .static
.static: $(SRCS) $(TSCS)
	echo "Code: $(SRCS)"
	echo "Test: $(TSCS)"
	$(VENV_PYTHON) -m mypy $^
	touch $@

test: venv lint static
	$(VENV_PYTHON) -m pytest
	
clean:
	rm -rf venv $(VENV_REQS)
	rm -rf .lint .static
	rm -f $(PACKAGE).tgz .tag
	-find src -type d -name __pycache__ -exec rm -fr "{}" \;
	git checkout -- $(TAG_FILES)

force-clean: clean
	rm -f requirements-test.txt
