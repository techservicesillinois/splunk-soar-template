#!/usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------
# Phantom sample App Connector python file
# -----------------------------------------

# Python 3 Compatibility imports
from __future__ import print_function, unicode_literals

# Phantom App imports
import phantom.app as phantom
from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult

import requests
import json
from bs4 import BeautifulSoup
from xml.dom import minidom

__version__ = 'GITHUB_TAG'
__git_hash__ = 'GITHUB_SHA'


class RetVal(tuple):

    def __new__(cls, val1, val2=None):
        return tuple.__new__(RetVal, (val1, val2))


class IllinoisMidpointConnector(BaseConnector):

    def __init__(self):

        # Call the BaseConnectors init first
        super(IllinoisMidpointConnector, self).__init__()

        self._state = None

        # Variable to hold a base_url in case the app makes REST calls
        # Do note that the app json defines the asset config, so please
        # modify this as you deem fit.
        self._base_url = None

    def _process_empty_response(self, response, action_result):
        if response.status_code == 200:
            return RetVal(phantom.APP_SUCCESS, {})

        return RetVal(
            action_result.set_status(
                phantom.APP_ERROR,
                "Empty response and no information in the header"),
            None)

    def _process_html_response(self, response, action_result):
        # An html response, treat it like an error
        status_code = response.status_code

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            error_text = soup.text
            split_lines = error_text.split('\n')
            split_lines = [x.strip() for x in split_lines if x.strip()]
            error_text = '\n'.join(split_lines)
        except BaseException:
            error_text = "Cannot parse error details"

        message = "Status Code: {0}. Data from server:\n{1}\n".format(
            status_code, error_text)

        message = message.replace(u'{', '{{').replace(u'}', '}}')
        return RetVal(action_result.set_status(
            phantom.APP_ERROR, message), None)

    def _process_json_response(self, r, action_result):
        # Try a json parse
        try:
            resp_json = r.json()
        except Exception as e:
            return RetVal(
                action_result.set_status(
                    phantom.APP_ERROR,
                    "Unable to parse JSON response. Error: {0}".format(
                        str(e))),
                None)

        # Please specify the status codes here
        if 200 <= r.status_code < 399:
            return RetVal(phantom.APP_SUCCESS, resp_json)

        # You should process the error returned in the json
        message = "Error from server. Status Code: "
        "{0} Data from server: {1}".format(
            r.status_code, r.text.replace(u'{', '{{').replace(u'}', '}}'))

        return RetVal(action_result.set_status(
            phantom.APP_ERROR, message), None)

    def _process_response(self, r, action_result):
        # store the r_text in debug data, it will get dumped in the logs if the
        # action fails
        if hasattr(action_result, 'add_debug_data'):
            action_result.add_debug_data({'r_status_code': r.status_code})
            action_result.add_debug_data({'r_text': r.text})
            action_result.add_debug_data({'r_headers': r.headers})

        # Process each 'Content-Type' of response separately

        # Process a json response
        if 'json' in r.headers.get('Content-Type', ''):
            return self._process_json_response(r, action_result)

        # Process an HTML response, Do this no matter what the api talks.
        # There is a high chance of a PROXY in between phantom and the rest of
        # world, in case of errors, PROXY's return HTML, this function parses
        # the error and adds it to the action_result.
        if 'html' in r.headers.get('Content-Type', ''):
            return self._process_html_response(r, action_result)

        # it's not content-type that is to be parsed, handle an empty response
        if not r.text:
            return self._process_empty_response(r, action_result)

        # everything else is actually an error at this point
        message = "Can't process response from server. Status Code: "
        "{0} Data from server: {1}".format(
            r.status_code, r.text.replace('{', '{{').replace('}', '}}'))

        return RetVal(action_result.set_status(
            phantom.APP_ERROR, message), None)

    def _handle_test_connectivity(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))

        self.save_progress("Connecting to endpoint")
        response = requests.get(
            f"{self._baseurl}/midpoint/ws/rest/self",
            headers={"Accept": "application/json"},
            allow_redirects=False,
            auth=self._auth
        )
        if response.json()["user"]["name"] != self._username:
            self.save_progress("Test Connectivity Failed.")
            return action_result.get_status()

        # Return success
        self.save_progress(
            f"Test Connectivity Passed: {__version__} ({__git_hash__[0:7]})")
        return action_result.set_status(phantom.APP_SUCCESS,
                                        "Active connection")

    def _handle_scramble_user(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))

        url = (f"{self._baseurl}/midpoint/model/rest/uofi/extended/users"
               f"/{param['uin']}/{param['netid']}/scramblePassword")
        headers = {
            "Content-Type": "application/xml",
            "user-agent": "SOAR"
        }
        xml = """<objectModification
                xmlns='http://midpoint.evolveum.com/xml/ns/public/common/api-types-3'
                xmlns:c='http://midpoint.evolveum.com/xml/ns/public/common/common-3'
                xmlns:t='http://prism.evolveum.com/xml/ns/public/types-3' />"""
        response = requests.patch(url, data=xml, headers=headers,
                                  allow_redirects=False, auth=self._auth)

        status = response.status_code
        reason = response.reason
        if status != 200:
            self.save_progress(f"User scramble failed:{status}:{reason}")
            return action_result.get_status()

        # Note: We have seen cases where the API does not return error messages
        # in cases we would expect to fail:
        #
        #   * If you swap UIN and NetID when passing those values in the URL
        #   * If you give a non-exisitent UIN and/or NetID
        #
        # There have been point-release updates since we saw this behavior.

        xmlDoc = minidom.parseString(response.content)
        userResetNodeList = xmlDoc.getElementsByTagNameNS(
            '*', "modifyTimestamp")
        userEmailNodeList = xmlDoc.getElementsByTagNameNS(
            '*', "selfserviceemail")

        userReset = None
        try:
            userReset = userResetNodeList[0].firstChild.nodeValue
        except IndexError:
            self.save_progress(
                f"No info returned from Midpoint for user {param['netid']}")
        except Exception:
            self.save_progress(
                f"Incomplete info from Midpoint for user {param['netid']}")

        try:
            self_service_email = userEmailNodeList[0].firstChild.nodeValue
            action_result.update_data(
                [{'self_service_email': self_service_email}])
        except IndexError:
            self.save_progress(
                "No self service email returned from Midpoint "
                f"for user {param['netid']}")

        if userReset:
            return action_result.set_status(
                phantom.APP_SUCCESS,
                f"User {param['netid']} scrambled {userReset}")
        else:
            return action_result.set_status(
                phantom.APP_SUCCESS,
                f"User {param['netid']} scrambled or invalid")

    def handle_action(self, param):
        ret_val = phantom.APP_SUCCESS

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == 'test_connectivity':
            ret_val = self._handle_test_connectivity(param)
        elif action_id == 'scramble_user':
            ret_val = self._handle_scramble_user(param)

        return ret_val

    def initialize(self):
        # Load the state in initialize, use it to store data
        # that needs to be accessed across actions
        self._state = self.load_state()

        # get the asset config
        config = self.get_config()
        """
        # Access values in asset config by the name

        # Required values can be accessed directly
        required_config_name = config['required_config_name']

        # Optional values should use the .get() function
        optional_config_name = config.get('optional_config_name')
        """

        self._hostname = config['hostname']
        self._port = config['port']
        self._auth = (config['username'], config['password'])
        self._baseurl = f"https://{self._hostname}:{self._port}"
        self._username = config['username']
        return phantom.APP_SUCCESS

    def finalize(self):
        # Save the state, this data is saved across actions and app upgrades
        self.save_state(self._state)
        return phantom.APP_SUCCESS


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
                IllinoisMidpointConnector._get_phantom_base_url() + '/login'

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

        connector = IllinoisMidpointConnector()
        connector.print_progress_message = True

        if session_id is not None:
            in_json['user_session_token'] = session_id
            connector._set_csrf_info(csrftoken, headers['Referer'])

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print(json.dumps(json.loads(ret_val), indent=4))

    exit(0)


if __name__ == '__main__':
    main()
