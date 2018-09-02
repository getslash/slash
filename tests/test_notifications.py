import sys
import slash

from slash.plugins import manager as plugin_manager


def test_notification_formatting():
    messages = []

    @slash.hooks.prepare_notification.register # pylint: disable=no-member
    def check_notification(message): # pylint: disable=unused-variable
        messages.append(message)

    plugin = plugin_manager.get_plugin('notifications')

    with slash.Session():
        try:
            raise Exception('Some message containing {curly_braces}')
        except Exception: # pylint: disable=broad-except
            plugin.entering_debugger(sys.exc_info())
    assert len(messages) == 1
    assert '{curly_braces}' in messages[0].get_short_message()
