from ..interface import PluginInterface
from ...conf import config
from ...ctx import session
from functools import partial
import requests


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


class Plugin(PluginInterface):
    def get_name(self):
        return "notifications"

    def activate(self):
        config.extend({
            "plugins": {
                "notifications" : {
                    "prowl_api_key" : None,
                    "nma_api_key" : None,
                    "pushbullet_api_key": None,
            }}})

    def deactivate(self):
        config["plugins"].pop("notifications")

    def session_end(self):
        self._notify("Session Ended", "Session {0} ended".format(session.id))

    def _notify(self, title, message):
        for func, api_key in [
                (partial(_post_notification, "https://prowl.weks.net/publicapi/add"), config.root.plugins.notifications.prowl_api_key),
                (partial(_post_notification, "https://www.notifymyandroid.com/publicapi/notify"), config.root.plugins.notifications.nma_api_key),
                (_pushbullet_notification, config.root.plugins.notifications.pushbullet_api_key),
                ]:
            if api_key is None:
                continue

            func(api_key, title, message)
