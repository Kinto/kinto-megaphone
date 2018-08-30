import pkg_resources
from . import megaphone

#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version


DEFAULT_SETTINGS = {}


def includeme(config):
    settings = config.get_settings()

    if 'megaphone.api_key' not in settings:
        raise TypeError("Megaphone API key must be provided as megaphone.api_key")
    api_key = settings['megaphone.api_key']

    if 'megaphone.url' not in settings:
        raise TypeError("Megaphone URL must be provided as megaphone.url")
    url = settings['megaphone.url']

    config.registry.megaphone = megaphone.Megaphone(url, api_key)

    config.add_api_capability(
        "megaphone",
        version=__version__,
        description="Send global broadcast messages to Megaphone on changes",
        url="https://github.com/glasserc/kinto-megaphone")

    # config.scan('kinto_megaphone.views')
