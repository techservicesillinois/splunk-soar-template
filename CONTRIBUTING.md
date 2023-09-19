# Contributing

This document aims to outline the requirements for the various forms of contribution for this project.

All contributions are subject to review via pull request.

## Working from the template repository.

> Remove this section from this document once these steps are completed.

- Replace all instances of APP_NAME in files
- Review the [application metadata][14] (app.json) 
  - add/remove configuration settings
  - add/remove actions
- add `SOAR_HOSTNAME` and `SOAR_TOKEN` to GitHub secrets for deployment
- add `WEBHOOK_URL` and `GITHUB_TOKEN` to GitHub secrets for chat reminders
- implement `test_connectivity` in `app.py`

[14]: https://docs.splunk.com/Documentation/Phantom/4.10.7/DevelopApps/Metadata

## Development Setup

### Setup PyEnv 

1. [Install PyEnv](https://github.com/pyenv/pyenv#basic-github-checkout)

2. Add PyEnv to your `.bash_profile`

```sh
export PYENV_ROOT=$HOME/.pyenv
PATH=$PATH:$HOME/.local/bin:$HOME/bin:$PYENV_ROOT/bin
export PATH
eval "$(pyenv init -)"
```

Note that this will not take effect unti your next login session.
In the meantime, you can `source ~/.bash_profile`.

### Run the test suite

Export the following variables
```sh
export APP_USERNAME="FAKE_USERNAME"
export APP_PASSWORD="FAKE_PASSWORD"
export APP_ENDPOINT="cybersecurity.illinois.edu/robots.txt"
export VCR_RECORD=1
```

```sh
pyenv install 3.9.13
pyenv local 3.9.13
make venv
source venv/bin/activate
make test
```

## Deployment

In GitHub, under 
`Secrets` then `Actions` add the following `Repository Secrets`:

`SOAR_HOSTNAME` set to `automate-illinois.soar.splunkcloud.com`
`SOAR_TOKEN` with your SOAR API token.

## Debugging

To emit a log into the SOAR debug logs, use `self.debug_print`:

    `self.debug_print("git_hash", __git_hash__)`

To read SOAR app DEBUG logs, visit SOAR `Administration` in the main drop-down, and look under `System Health` and then `Debugging`. 

> Tip: You must have specific permissions assigned to your account to access this area.

Set 'Log Range' to 'Recent Logs'. Click 'Download log.
Unzip the `.tgz` file with your preferred unzip solution.
SOAR logs are in the phantom folders, nested pretty deep.
Deployment logs are in `app_install`.

> For SOAR app logs, you may need to check multiple files, based on which broker your code ran on.
