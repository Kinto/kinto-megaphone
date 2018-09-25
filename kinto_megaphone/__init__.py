import pkg_resources

#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version

from collections import namedtuple
from pyramid.config import ConfigurationError
from pyramid.settings import aslist

from .heartbeat import MegaphoneHeartbeat
from .megaphone import Megaphone


MegaphoneConfig = namedtuple('MegaphoneConfig', ['api_key', 'url', 'broadcaster_id'])


def validate_config(config, prefix):
    settings = config.get_settings()

    if prefix + 'api_key' not in settings:
        raise ConfigurationError("Megaphone API key must be provided for {}".format(prefix))
    api_key = settings[prefix + 'api_key']

    if prefix + 'url' not in settings:
        raise ConfigurationError("Megaphone URL must be provided for {}".format(prefix))
    url = settings[prefix + 'url']

    if prefix + 'broadcaster_id' not in settings:
        raise ConfigurationError("Megaphone broadcaster_id must be provided for {}".format(prefix))
    broadcaster_id = settings[prefix + 'broadcaster_id']

    return MegaphoneConfig(api_key, url, broadcaster_id)


def find_megaphone_prefix(registry):
    # FIXME: this assumes only one Megaphone server per config
    listeners = aslist(registry.settings['event_listeners'])
    for listener in listeners:
        prefix = 'event_listeners.{}.'.format(listener)
        listener_modpath = registry.settings['{}use'.format(prefix)]
        # FIXME: maybe be smarter about the current module's path?
        if listener_modpath.startswith('kinto_megaphone.'):
            return prefix

    raise ConfigurationError(
        "No megaphone listeners configured. Listeners are {}".format(listeners))


def includeme(config):
    prefix = find_megaphone_prefix(config.registry)
    mp_config = validate_config(config, prefix)
    anon_client = Megaphone(mp_config.url, None)

    config.registry.heartbeats['megaphone'] = MegaphoneHeartbeat(anon_client)
    config.add_api_capability(
        "megaphone",
        version=__version__,
        description="Broadcast collection updates via megaphone",
        url="https://github.com/Kinto/kinto-megaphone")
