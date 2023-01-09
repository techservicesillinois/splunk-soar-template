import datetime
import gzip
import json
import jwt
import logging
import os

import pytest
import vcr

from phillinois_app import AppConnector
from vcr.serializers import yamlserializer

# Required pytest plugins
pytest_plugins = ("splunk-soar-connectors")

CASSETTE_USERNAME = "FAKE_USERNAME"
CASSETTE_PASSWORD = "FAKE_PASSWORD"
CASSETTE_NETID = 'thor2'
CASSETTE_ENDPOINT = "help.uillinois.edu"
CASSETTE_ACCOUNT_NAME = "None/Not Found"  # TODO: Pull from config as part of issue #13
CASSETTE_ORG_NAME = "Marvel U"
CASSETTE_TIMEZONE = "0000"
CASSETTE_LOG_LEVEL = "DEBUG"
APPID = 66  # APPID and URL are also CASSETTE but need short names
URL = f"https://{CASSETTE_ENDPOINT}"

# To record, `export VCR_RECORD=True`
VCR_RECORD = "VCR_RECORD" in os.environ


class CleanYAMLSerializer:
    def serialize(cassette: dict):
        for interaction in cassette['interactions']:
            clean_token(interaction)
            clean_search(interaction)
            clean_new_ticket(interaction)
            clean_people_lookup(interaction)
        return yamlserializer.serialize(cassette)

    def deserialize(cassette: str):
        return yamlserializer.deserialize(cassette)


def clean_token(interaction: dict):
    uri = f"{URL}/SBTDWebApi/api/auth"
    if interaction['request']['uri'] != uri:
        return

    token = jwt.encode(
        {'exp': datetime.datetime(2049, 6, 25)}, 'arenofun', algorithm='HS256')
    response = interaction['response']
    if 'Content-Encoding' in response['headers'].keys() and \
            response['headers']['Content-Encoding'] == ['gzip']:
        token = gzip.compress(bytes(token, "ascii"))
    response['body']['string'] = token


def clean_search(interaction: dict):
    uri = f"{URL}/SBTDWebApi/api/accounts/search"
    if interaction['request']['uri'] != uri:
        return

    body = json.loads(interaction['response']['body']['string'])
    result = {}
    for item in body:
        if item['Name'] == CASSETTE_ACCOUNT_NAME:
            result = item
    body = [result]

    interaction['response']['body']['string'] = json.dumps(body)


def clean_new_ticket(interaction: dict):
    id = 564073
    uri = f"{URL}/SBTDWebApi/api/{APPID}/tickets/?EnableNotifyReviewer=False" + \
        "&NotifyRequestor=False&NotifyResponsible=False" + \
        "&AllowRequestorCreation=False"

    if interaction['request']['uri'] != uri:
        return

    body = json.loads(interaction['response']['body']['string'])
    body['Uri'] = body['Uri'].replace(str(body['ID']), str(id))
    body['ID'] = id
    body['RequestorEmail'] = 'nobody@example.com'
    body['RequestorName'] = 'Jane Foster'
    body['RequestorFirstName'] = 'Jane'
    body['RequestorLastName'] = 'Foster'
    body['RequestorPhone'] = None

    body['Notify'][0]['Name'] = 'Jane Foster'
    body['Notify'][0]['Value'] = 'nobody@example.com'
    interaction['response']['body']['string'] = json.dumps(body)


def clean_people_lookup(interaction: dict):
    # TODO: Switch the NetID here based on ENV settings and record mode
    netid = os.environ.get('TDX_NETID', CASSETTE_NETID)
    uri = "%s/SBTDWebApi/api/people/lookup?searchText=%s&maxResults=1"

    if interaction['request']['uri'] != uri % (URL, netid):
        return

    interaction['request']['uri'] = uri % (URL, 'thor2')
    body = json.loads(interaction['response']['body']['string'])

    body[0]['Salutation'] = 'Doctor'
    body[0]['FirstName'] = 'Jane'
    body[0]['LastName'] = 'Foster'
    body[0]['MiddleName'] = None
    body[0]['FullName'] = 'Jane Foster'
    body[0]['Nickname'] = 'The Mighty Thor'

    body[0]['HomePhone'] = None
    body[0]['PrimaryPhone'] = None
    body[0]['WorkPhone'] = None
    body[0]['OtherPhone'] = None
    body[0]['MobilePhone'] = None

    body[0]['PrimaryEmail'] = 'nobody@example.com'
    body[0]['AlternateEmail'] = 'nobody@example.com'
    body[0]['AlertEmail'] = 'nobody@example.com'

    interaction['response']['body']['string'] = json.dumps(body)


@pytest.fixture
def connector(monkeypatch) -> TdxConnector:
    conn = TdxConnector()
    if not VCR_RECORD:  # Always use cassette values when using cassette
        #  TODO: Lots more configs!
        conn.config = {
            "username": CASSETTE_USERNAME,
            "password": CASSETTE_PASSWORD,
            "endpoint": CASSETTE_ENDPOINT,
            "appid": APPID,
            "orgname": CASSETTE_ORG_NAME,
            "timezone": CASSETTE_TIMEZONE,
            "loglevel": CASSETTE_LOG_LEVEL,
            "sandbox": True,
        }
        os.environ.pop('TDX_NETID', None)
    else:  # User environment values
        env_keys = ['username','password','netid',
                    'endpoint','appid', 'orgname',
                    'timezone', 'loglevel']

        for key in env_keys:
            env_key = f"TDX_{key.upper()}"
            conn.config[key] = os.environ.get(env_key, None)
            if not conn.config[key]:
                raise ValueError(f'{env_key} unset or empty with record mode')
        
        conn.config['sandbox'] = True  # Always True - no testing in production.

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
