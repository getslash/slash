from ..interface import PluginInterface
from ... import hooks
from ...conf import config
from ...ctx import session
from ...exception_handling import handling_exceptions
from ...utils.conf_utils import Cmdline

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from vintage import warn_deprecation
import datetime
from pkg_resources import resource_string
import requests
import slash
import smtplib
import jinja2


_SLASH_ICON = "http://slash.readthedocs.org/en/latest/_static/slash-logo.png"

def _post_request(url, **kwargs):
    response = requests.post(url, **kwargs)
    response.raise_for_status()
    return response


def _send_email(smtp_server, subject, body, from_email, to_list, cc_list):
    """Send an email.

    :param str smtp_server: The smtp_server uri
    :param str subject: The email subject.
    :param str body: The email body.
    :param str from_email: The from address.
    :param list to_list: A list of email addresses to send to.
    :param list cc_list: A list of email addresses to send to as cc.
    """
    msg = MIMEMultipart('alternative')
    msg.attach(MIMEText(body, 'html'))

    if not to_list:
        to_list = []

    if not cc_list:
        cc_list = []

    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ', '.join(to_list)
    msg['Cc'] = ', '.join(cc_list)
    smtp = smtplib.SMTP(smtp_server, timeout=30)
    try:
        smtp.sendmail(from_email, to_list + cc_list, msg.as_string())
    finally:
        smtp.quit()


class Message(object):
    def __init__(self, title, body_template, kwargs, is_pdb):
        self.title = title
        self.body = body_template
        self.kwargs = kwargs
        self.details_dict = {}
        self.is_pdb = is_pdb

    def get_title(self):
        return self.title.format(**self.kwargs)

    def get_short_message(self):
        return self.body.format(**self.kwargs)

    _email_template = None

    def _get_html_template(self):
        returned = self._email_template
        if returned is None:
            source = resource_string('slash.plugins.builtin', 'email_template.j2').decode('utf-8')
            returned = type(self)._email_template = jinja2.Template(source)
        return returned

    def get_html_message(self):
        return self._get_html_template().render(message=self, **self.kwargs)



class Plugin(PluginInterface):
    """Enables notifications for successful and failed test runs through various providers (NMA, Prowl, Pushover etc.)
    For more information see https://slash.readthedocs.org/en/master/builtin_plugins.html#notifications
    """

    def __init__(self, *args, **kwargs):
        super(Plugin, self).__init__(*args, **kwargs)
        self._notifiers = {}
        self._basic_config = {
            "prowl_api_key" : None,
            "nma_api_key" : None,
            "pushbullet_api_key": None,
            "notification_threshold": 5,
            "notify_only_on_failures": False // Cmdline(on='--notify-only-on-failures'),
            "notify_on_pdb": True,
        }
        self._add_notifier(self._prowl_notifier, 'prowl', {'api_key': None, 'enabled': True})
        self._add_notifier(self._nma_notifier, 'nma', {'api_key': None, 'enabled': True})
        self._add_notifier(self._pushbullet_notifier, 'pushbullet', {'api_key': None, 'enabled': True})
        self._add_notifier(self._email_notifier, 'email', {
            'from_email': 'Slash <noreply@getslash.github.io>',
            'smtp_server': None,
            'to_list': [] // Cmdline(append='--email-to', metavar='ADDRESS'),
            'cc_list': []
        })
        self._add_notifier(self._slack_notifier, 'slack', {'url': None, 'channel': None, 'from_user': 'slash-bot'})

    def get_name(self):
        return 'notifications'

    def get_default_config(self):
        return self._basic_config

    def _add_notifier(self, func, name, conf_dict=None):
        self._notifiers[name] = func
        if not conf_dict:
            conf_dict = {}
        assert isinstance(conf_dict, dict)
        conf_dict.setdefault('enabled', False)
        conf_dict['enabled'] //= Cmdline(on='--notify-{}'.format(name))
        self._basic_config[name] = conf_dict

    def _get_from_config_with_legacy(self, notifier_name, legacy_name, new_name):
        this_config = config.get_path('plugin_config.notifications')
        value = this_config[legacy_name]
        if value:
            warn_deprecation('{} is depreacted. use {}.{} instead'.format(legacy_name, notifier_name, new_name))
        else:
            value = this_config[notifier_name][new_name]
        return value

    @staticmethod
    def _os_post_notification(url, api_key, message):
        if api_key:
            data = {
                "apikey": api_key,
                "application": "slash",
                "event": message.get_title(),
                "description": message.get_short_message(),
            }
            _post_request(url, data=data)

    def _prowl_notifier(self, message):
        api_key = self._get_from_config_with_legacy('prowl', 'prowl_api_key', 'api_key')
        self._os_post_notification("https://prowl.weks.net/publicapi/add", api_key, message)

    def _nma_notifier(self, message):
        api_key = self._get_from_config_with_legacy('nma', 'nma_api_key', 'api_key')
        self._os_post_notification("https://www.notifymyandroid.com/publicapi/notify", api_key, message)

    def _pushbullet_notifier(self, message):
        api_key = self._get_from_config_with_legacy('pushbullet', 'pushbullet_api_key', 'api_key')
        if api_key:
            data = {"type": "note", "title": message.get_title(), "body": message.get_short_message()}
            _post_request("https://api.pushbullet.com/api/pushes", data=data, auth=(api_key, ""))

    def _email_notifier(self, message):
        email_config = config.root.plugin_config.notifications.email
        email_kwargs = {
            'from_email': email_config.from_email,
            'subject': message.get_title(),
            'body': message.get_html_message(),
            'smtp_server': email_config.smtp_server,
            'to_list': email_config.to_list or None,
            'cc_list': email_config.cc_list,
        }
        if all(value is not None for value in email_kwargs.values()):
            _send_email(**email_kwargs)

    def _slack_notifier(self, message):
        slack_config = config.root.plugin_config.notifications.slack
        if (slack_config.url is None) or (slack_config.channel is None):
            return

        color = '#439FE0' if message.is_pdb else ('good' if self._finished_successfully() else 'danger')
        kwargs = {
            'attachments': [{
                'title': message.get_title(),
                'fallback': 'Session {session_id} {result}'.format(**message.kwargs),
                'text': message.get_short_message(),
                'color': color,
                }],
            'channel': slack_config.channel,
            'username': slack_config.from_user,
            'icon_url': _SLASH_ICON,
            }
        _post_request(slack_config.url, json=kwargs)

    def _finished_successfully(self):
        return session.results.is_success(allow_skips=True)

    def _get_message(self, short_message, is_pdb):
        result_str = 'entered PDB' if is_pdb else ("Succeeded" if self._finished_successfully() else "Failed")
        kwargs = {
            'session_id': session.id,
            'host_name': session.host_name,
            'full_name': 'N/A',
            'duration': str(datetime.timedelta(seconds=session.duration)).partition('.')[0],
            'result': result_str,
            'success': self._finished_successfully(),
            'results_summary': repr(session.results).replace('<', '').replace('>', ''),
            'total_num_tests': session.results.get_num_results(),
            'non_successful_tests': session.results.get_num_errors() + session.results.get_num_failures(),
        }
        backslash_plugin = slash.plugins.manager.get_active_plugins().get('backslash')
        if backslash_plugin:
            config.root.plugin_config.notifications.email.to_list.append(backslash_plugin.session.user_email)
            url = backslash_plugin.webapp_url + 'sessions/{}'.format(session.id)
            kwargs['backslash_link'] = url
            kwargs['full_name'] = backslash_plugin.session.user_display_name
            session_info = 'Backslash: {backslash_link}'
        else:
            session_info = 'Session ID: {session_id}'
        short_message += "\n\n" + session_info
        title = "Slash Session on {host_name} has {result}".format(**kwargs)
        kwargs['title'] = title
        return Message(title, short_message, kwargs, is_pdb)

    def entering_debugger(self, exc_info):
        if not self.current_config.notify_on_pdb:
            return
        self._notify_all(short_message=repr(exc_info[1]), is_pdb=True)

    def session_end(self):
        if session.duration < self.current_config.notification_threshold:
            return
        if self._finished_successfully() and self.current_config.notify_only_on_failures:
            return
        self._notify_all(short_message='{results_summary}', is_pdb=False)


    def _notify_all(self, short_message, is_pdb):
        message = self._get_message(short_message, is_pdb)
        hooks.prepare_notification(message=message) # pylint: disable=no-member
        this_config = config.get_path('plugin_config.notifications')

        for notifier_name, notifier_func in self._notifiers.items():
            if not this_config[notifier_name]['enabled']:
                continue
            with handling_exceptions(swallow=True):
                notifier_func(message)
