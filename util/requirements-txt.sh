#!/bin/bash
# Install the desired Python version with `pyenv` or `uv`
# Pass in the desired Python version as $1 (i.e. 3.13)

# Use `uv`, if available
# uv may use any python versions from pyenv if installed, but it can also install versions itself.
if command -v uv >/dev/null 2>&1
then
	$(uv python find) -m venv $1
	exit 0
fi

# Use `pyenv` if available
if command -v pyenv >/dev/null 2>&1
then
	python3 -m venv $1
	exit 0
fi

# Failed - raise an error if used in CI/CD
echo "Unable to find either `pyenv` or `uv`."
echo "Install either and re-run or set your .python-version to continue."
exit 1
