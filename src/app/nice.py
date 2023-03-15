# -----------------------------------------
# Nice and dry Phantom App
# -----------------------------------------
# TODO: This SHOULD be split into its own repo and imported
import inspect

# Phantom App imports
import phantom.app as phantom
from phantom.base_connector import BaseConnector


def handle(*action_ids):
    """Registor function to handle given action_ids."""
    def decorator(func):
        func._handle = action_ids
        return func
    return decorator


class NiceBaseConnector(BaseConnector):

    def __init__(self):
        super(NiceBaseConnector, self).__init__()

        self.actions = {}
        for _, method in inspect.getmembers(self):
            if hasattr(method, '_handle'):
                for action_id in getattr(method, '_handle'):
                    self.actions[action_id] = method

        self._state = None

    def handle_action(self, param):
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id in self.actions.keys():
            return self.actions[action_id](param)

        return phantom.APP_SUCCESS  # TODO: Should this be an error instead?

    def initialize(self):
        # Load the state in initialize, use it to store data
        # that needs to be accessed across actions
        self._state = self.load_state()

        return phantom.APP_SUCCESS

    def finalize(self):
        # Save the state, this data is saved across actions and app upgrades
        self.save_state(self._state)
        return phantom.APP_SUCCESS
