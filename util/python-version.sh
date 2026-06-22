#!/bin/bash
# Install the desired Python version with `pyenv` or `uv`
# Pass in the desired Python version as $1 (i.e. 3.13)

# Use `pyenv` if available
if command -v pyenv >/dev/null 2>&1
then
	echo "Using pyenv to create .python-version"
	pyenv install -s $1
	pyenv local $1
	exit 0
fi

# Use `uv`, if available
if command -v uv >/dev/null 2>&1
then
	echo "Using uv to create .python-version"
	uv python install $1
	uv python pin $1
	exit 0
fi

# Failed - raise an error if used in CI/CD
echo "Unable to find either `pyenv` or `uv`."
echo "Install either and re-run or set your .python-version to continue."
exit 1
