import json

from app import AppConnector

APP_ID = "tacosalad"


def test_connectivity(cassette, connector: AppConnector):
    in_json = {
            "appid": APP_ID,
            "identifier": "test_connectivity",
            "parameters": [{}],
    }

    result = json.loads(connector._handle_action(json.dumps(in_json), None))
    assert result[0]["message"] == "Active connection"


def test_failed_connectivity(cassette, connector: AppConnector):
    in_json = {
            "appid": APP_ID,
            "identifier": "test_connectivity",
            "parameters": [{}],
    }

    result = json.loads(connector._handle_action(json.dumps(in_json), None))
    assert result[0]["message"] == "Failed connection"
