import logging
import os

import pytest
import vcr

from phtoolbox.app import AppConnector
from vcr_cleaner import CleanYAMLSerializer

# Required pytest plugins
pytest_plugins = ("splunk-soar-connectors")

CASSETTE_USERNAME = "FAKE_USERNAME"
CASSETTE_PASSWORD = "FAKE_PASSWORD"
CASSETTE_ENDPOINT = "cybersecurity.illinois.edu/robots.txt"

# To record, `export VCR_RECORD=True`
VCR_RECORD = "VCR_RECORD" in os.environ


@pytest.fixture
def connector(monkeypatch) -> AppConnector:
    conn = AppConnector()
    if not VCR_RECORD:  # Always use cassette values when using cassette
        conn.config = {
            "username": CASSETTE_USERNAME,
            "password": CASSETTE_PASSWORD,
            "endpoint": CASSETTE_ENDPOINT,git@github.com:techservicesillinois/SecOps-Tools.git
        }
    else:  # User environment values
        env_keys = ['username', 'password', 'endpoint']

        for key in env_keys:
            env_key = f"APP_{key.upper()}"
            conn.config[key] = os.environ.get(env_key, None)
            if not conn.config[key]:
                raise ValueError(f'{env_key} unset or empty with record mode')

    conn.logger.setLevel(logging.INFO)
    return conn


@pytest.fixture
def cassette(request) -> vcr.cassette.Cassette:
    my_vcr = vcr.VCR(
        cassette_library_dir='cassettes',
        record_mode='once' if VCR_RECORD else 'none',
        # TODO: Uncomment with remove_creds from shared repo
        # before_record_request=remove_creds,
        filter_headers=[('Authorization', 'Bearer FAKE_TOKEN')],
        match_on=['uri', 'method'],
    )

    # TODO: Remove this block if not using cleaners
    # (see https://github.com/techservicesillinois/vcrpy-cleaner):
    yaml_cleaner = CleanYAMLSerializer()
    my_vcr.register_serializer("cleanyaml", yaml_cleaner)
    # TODO: Register cleaner functions here:
    # yaml_cleaner.register_cleaner(clean_bad_word)

    with my_vcr.use_cassette(f'{request.function.__name__}.yaml',
                             serializer="cleanyaml") as tape:
        yield tape
        if my_vcr.record_mode == 'none':  # Tests only valid when not recording
            assert tape.all_played, \
                f"Only played back {len(tape.responses)} responses"
