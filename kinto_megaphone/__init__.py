import pkg_resources


#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version


DEFAULT_SETTINGS = {}


def includeme(config):
    settings = config.get_settings()

    defaults = {k: v for k, v in DEFAULT_SETTINGS.items() if k not in settings}
    config.add_settings(defaults)

    config.add_api_capability(
        "megaphone",
        version=__version__,
        description="Send global broadcast messages to Megaphone on changes",
        url="https://github.com/glasserc/kinto-megaphone")

    # config.scan('kinto_megaphone.views')
