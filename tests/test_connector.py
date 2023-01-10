import json
from urllib.error import HTTPError

from vcr import cassette

from requests.exceptions import HTTPError

from phTDX.tdx_connector import TdxConnector

APP_ID = "tacosalad"

def test_connectivity(cassette, connector: TdxConnector):
    in_json = {
            "appid": APP_ID,
            "identifier": "test_connectivity",
            "parameters": [{}], # TODO: Submit an issue asking to allow [] here.
    }

    result = json.loads(connector._handle_action(json.dumps(in_json), None))
    assert result[0]["message"] == "Active connection"


def test_failed_connectivity(cassette, connector: TdxConnector):
    in_json = {
            "appid": APP_ID,
            "identifier": "test_connectivity",
            "parameters": [{}],
    }

    result = json.loads(connector._handle_action(json.dumps(in_json), None))
    assert result[0]["message"] == "Failed connection"
