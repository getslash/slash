from ..interface import PluginInterface
from ...conf import config
from ...ctx import session
import requests

class Plugin(PluginInterface):
    def get_name(self):
        return "notifications"

    def activate(self):
        config.extend({
            "plugins": {
                "notifications" : {
                    "prowl_api_key" : None,
                    "nma_api_key" : None,
            }}})

    def deactivate(self):
        config["plugins"].pop("notifications")

    def session_end(self):
        self._notify("Session Ended", "Session {0} ended".format(session.id))

    def _notify(self, title, message):
        for url, api_key in [
                ("https://prowl.weks.net/publicapi/add", config.root.plugins.notifications.prowl_api_key),
                ("https://www.notifymyandroid.com/publicapi/notify", config.root.plugins.notifications.nma_api_key),
                ]:
            if api_key is None:
                continue
            resp = requests.post(url, {"apikey": api_key, "application": "slash", "event": title, "description": message})
            resp.raise_for_status()
