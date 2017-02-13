from ..interface import PluginInterface
from ...conf import config
from ...ctx import session
from functools import partial
import time
import socket
import requests
import gossip


def _post_notification(url, api_key, title, message):
    response = requests.post(url, {"apikey": api_key, "application": "slash", "event": title, "description": message})
    response.raise_for_status()


def _pushbullet_notification(api_key, title, message):
    data = {
        "type": "note",
        "title": title,
        "body": message
    }
    response = requests.post(
        "https://api.pushbullet.com/api/pushes",
        data=data,
        auth=(api_key, ""))
    response.raise_for_status()


class Message(object):
    def __init__(self, title, body):
        self.title = title
        self.body = body


class Plugin(PluginInterface):
    """Enables notifications for successful and failed test runs through various providers (NMA, Prowl, Pushover etc.)
    For more information see https://slash.readthedocs.org/en/master/builtin_plugins.html#notifications
    """

    def get_name(self):
        return "notifications"

    def get_config(self):
        return {
            "prowl_api_key" : None,
            "nma_api_key" : None,
            "pushbullet_api_key": None,
            "notification_threshold": 5,
        }

    def session_start(self):
        self._session_start_time = time.time() #pylint: disable=W0201

    def session_end(self):
        if time.time() - self._session_start_time < config.root.plugin_config.notifications.notification_threshold:
            return

        result = "successfully" if session.results.is_success() else "unsuccessfully"
        hostname = socket.gethostname().split(".")[0]
        body = "{0}\n\n{1}".format(session.results, session.id)

        message = Message("Slash session in {0} ended {1}".format(hostname, result), body)
        gossip.trigger("slash-gossip.prepare_notification", message=message)

        self._notify(message.title, message.body)

    def _notify(self, title, message):
        this_config = config.root.plugin_config.notifications
        for func, api_key in [
                (partial(_post_notification, "https://prowl.weks.net/publicapi/add"), this_config.prowl_api_key),
                (partial(_post_notification, "https://www.notifymyandroid.com/publicapi/notify"), this_config.nma_api_key),
                (_pushbullet_notification, this_config.pushbullet_api_key),
                ]:
            if api_key is None:
                continue

            func(api_key, title, message)
