import pkg_resources

#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version

from .heartbeat import find_megaphone_url, MegaphoneHeartbeat
from .megaphone import Megaphone

def includeme(config):
    anon_client = Megaphone(find_megaphone_url(config.registry), None)

    config.registry.heartbeats['megaphone'] = MegaphoneHeartbeat(anon_client)
