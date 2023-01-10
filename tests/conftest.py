import datetime
import gzip
import json
import jwt
import logging
import os

import pytest
import vcr

from phillinois_app.app import AppConnector
from vcr.serializers import yamlserializer

# Required pytest plugins
pytest_plugins = ("splunk-soar-connectors")

CASSETTE_USERNAME = "FAKE_USERNAME"
CASSETTE_PASSWORD = "FAKE_PASSWORD"
CASSETTE_NETID = 'thor2'
CASSETTE_ENDPOINT = "help.uillinois.edu"
URL = f"https://{CASSETTE_ENDPOINT}"

# To record, `export VCR_RECORD=True`
VCR_RECORD = "VCR_RECORD" in os.environ


class CleanYAMLSerializer:
    @staticmethod
    def serialize(cassette: dict):
        for interaction in cassette['interactions']:
            clean_jwt_token(interaction)
        return yamlserializer.serialize(cassette)

    @staticmethod
    def deserialize(cassette: str):
        return yamlserializer.deserialize(cassette)


def clean_jwt_token(interaction: dict):
    uri = f"{URL}/api/auth"  # TODO: Adjust URI to match auth URL in use.
    if interaction['request']['uri'] != uri:
        return

    token = jwt.encode(
        {'exp': datetime.datetime(2049, 6, 25)}, 'arenofun', algorithm='HS256')
    response = interaction['response']
    if 'Content-Encoding' in response['headers'].keys() and \
            response['headers']['Content-Encoding'] == ['gzip']:
        token = gzip.compress(bytes(token, "ascii"))
    response['body']['string'] = token


@pytest.fixture
def connector(monkeypatch) -> AppConnector:
    conn = AppConnector()
    if not VCR_RECORD:  # Always use cassette values when using cassette
        conn.config = {
            "username": CASSETTE_USERNAME,
            "password": CASSETTE_PASSWORD,
            "endpoint": CASSETTE_ENDPOINT,
        }
    else:  # User environment values
        env_keys = ['username', 'password',
                    'netid', 'endpoint']

        for key in env_keys:
            # TODO: Change APP_ on next line to avoid key conflicts
            env_key = f"APP_{key.upper()}"
            conn.config[key] = os.environ.get(env_key, None)
            if not conn.config[key]:
                raise ValueError(f'{env_key} unset or empty with record mode')

    conn.logger.setLevel(logging.INFO)
    return conn


def remove_creds(request):
    if not request.body:
        return request
    data = json.loads(request.body.decode('utf-8'))

    if 'password' in data:
        data['password'] = CASSETTE_PASSWORD
    if 'username' in data:
        data['username'] = CASSETTE_USERNAME

    request.body = json.dumps(data)
    return request


@pytest.fixture
def cassette(request) -> vcr.cassette.Cassette:
    my_vcr = vcr.VCR(
        cassette_library_dir='cassettes',
        record_mode='once' if VCR_RECORD else 'none',
        before_record_request=remove_creds,
        filter_headers=[('Authorization', 'Bearer FAKE_TOKEN')],
        match_on=['uri', 'method'],
    )
    my_vcr.register_serializer("cleanyaml", CleanYAMLSerializer)

    with my_vcr.use_cassette(f'{request.function.__name__}.yaml',
                             serializer="cleanyaml") as tape:
        yield tape
        if my_vcr.record_mode == 'none':  # Tests only valid when not recording
            assert tape.all_played, \
                f"Only played back {len(tape.responses)} responses"
