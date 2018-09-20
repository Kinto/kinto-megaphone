from pyramid.config import ConfigurationError
from pyramid.settings import aslist


class MegaphoneHeartbeat(object):
    def __init__(self, client):
        self.client = client

    def __call__(self, _request):
        data = self.client.heartbeat()
        return data['database'] == 'ok' and data['status'] == 'ok'


def find_megaphone_url(registry):
    # FIXME: this assumes only one Megaphone server per config
    listeners = aslist(registry.settings['event_listeners'])
    for listener in listeners:
        prefix = 'event_listeners.{}'.format(listener)
        listener_modpath = registry.settings['{}.use'.format(prefix)]
        # FIXME: maybe be smarter about the current module's path?
        if listener_modpath.startswith('kinto_megaphone.'):
            return registry.settings['{}.url'.format(prefix)]

    raise ConfigurationError(
        "No megaphone listeners configured. Listeners are {}".format(listeners))
