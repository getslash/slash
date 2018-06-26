import slash

from slash.plugins import manager as plugin_manager


def test_notification_formatting():
    plugin = plugin_manager.get_plugin('notifications')
    with slash.Session():
        msg = plugin._get_message('{bla}', True) # pylint: disable=protected-access
    assert msg.get_title()
    assert '{bla}' in msg.get_short_message()
    assert msg.get_html_message()
