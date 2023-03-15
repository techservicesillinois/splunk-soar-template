#!/usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------
# Phantom sample App Connector python file
# -----------------------------------------

# Phantom App imports
import phantom.app as phantom
from phantom.action_result import ActionResult

import requests
import json

from .nice import NiceBaseConnector, handle

__version__ = 'GITHUB_TAG'
__git_hash__ = 'GITHUB_SHA'
__build_time__ = 'BUILD_TIME'


class AppConnector(NiceBaseConnector):

    @handle('test_connectivity', 'test_robots_txt')
    def _handle_test_connectivity(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))

        self.save_progress("Connecting to endpoint")
        response = requests.get(
            self._baseurl,
            allow_redirects=True,
        )
        if response.status_code != 200:
            self.save_progress("Test Connectivity Failed.")
            return action_result.set_status(phantom.APP_ERROR,
                                            "Failed connection")

        # Return success
        self.save_progress(
            f"Test Connectivity Passed: {__version__} ({__git_hash__[0:7]})")
        return action_result.set_status(phantom.APP_SUCCESS,
                                        "Active connection")

    def initialize(self):
        ret = super(AppConnector, self).initialize()

        # get the asset config
        config = self.get_config()
        """
        # Access values in asset config by the name

        # Required values can be accessed directly
        required_config_name = config['required_config_name']

        # Optional values should use the .get() function
        optional_config_name = config.get('optional_config_name')
        """

        self._endpoint = config['endpoint']
        self._auth = (config['username'], config['password'])
        self._baseurl = f"https://{self._endpoint}"
        self._username = config['username']

        return ret


def main():
    import argparse

    argparser = argparse.ArgumentParser()

    argparser.add_argument('input_test_json', help='Input Test JSON file')
    argparser.add_argument('-u', '--username', help='username', required=False)
    argparser.add_argument('-p', '--password', help='password', required=False)

    args = argparser.parse_args()
    session_id = None

    username = args.username
    password = args.password

    if username is not None and password is None:

        # User specified a username but not a password, so ask
        import getpass
        password = getpass.getpass("Password: ")

    if username and password:
        try:
            login_url = \
                AppConnector._get_phantom_base_url() + '/login'

            print("Accessing the Login page")
            r = requests.get(login_url, verify=False)
            csrftoken = r.cookies['csrftoken']

            data = dict()
            data['username'] = username
            data['password'] = password
            data['csrfmiddlewaretoken'] = csrftoken

            headers = dict()
            headers['Cookie'] = 'csrftoken=' + csrftoken
            headers['Referer'] = login_url

            print("Logging into Platform to get the session id")
            r2 = requests.post(login_url, verify=False,
                               data=data, headers=headers)
            session_id = r2.cookies['sessionid']
        except Exception as e:
            print(f"Unable to get session id from the platform. Error: {e}")
            exit(1)

    with open(args.input_test_json) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = AppConnector()
        connector.print_progress_message = True

        if session_id is not None:
            in_json['user_session_token'] = session_id
            connector._set_csrf_info(csrftoken, headers['Referer'])

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print(json.dumps(json.loads(ret_val), indent=4))

    exit(0)


if __name__ == '__main__':
    main()
