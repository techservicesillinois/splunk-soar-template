import json

from phtoolbox.app.base_connector import NiceBaseConnector

APP_ID = "tacosalad"


def test_connectivity(cassette, connector: NiceBaseConnector):
    in_json = {
            "appid": APP_ID,
            "identifier": "test_connectivity",
            "parameters": [{}],
    }

    result = json.loads(connector.nice_handle_action(json.dumps(in_json)))
    assert result[0]["message"] == "Active connection"


def test_failed_connectivity(cassette, connector: NiceBaseConnector):
    in_json = {
            "appid": APP_ID,
            "identifier": "test_connectivity",
            "parameters": [{}],
    }

    result = json.loads(connector.nice_handle_action(json.dumps(in_json)))
    assert result[0]["message"] == "Failed connection"
