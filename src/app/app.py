#!/usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------
# Phantom sample App Connector python file
# -----------------------------------------

# Phantom App imports
import phantom.app as phantom
from phantom.action_result import ActionResult

import requests

from phtoolbox.app.base_connector import NiceBaseConnector, handle

__version__ = 'GITHUB_TAG'
__git_hash__ = 'GITHUB_SHA'
__build_time__ = 'BUILD_TIME'


class AppConnector(NiceBaseConnector):

    @handle('test_connectivity', 'test_robots_txt')
    def _handle_test_connectivity(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))

        self.save_progress("Connecting to endpoint")
        response = requests.get(
            self._api_url,
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
        self._api_url = f"https://{self._endpoint}"
        self._username = config['username']

        return ret
