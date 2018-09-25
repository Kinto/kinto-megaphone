import mock
import pytest
from pyramid.config import ConfigurationError
import kinto_megaphone


def test_find_megaphone_url_reads_settings():
    registry = mock.Mock()
    registry.settings = {
        'event_listeners': 'mp',
        'event_listeners.mp.use': 'kinto_megaphone.listeners',
        'event_listeners.mp.url': 'http://example.com/',
    }

    assert kinto_megaphone.find_megaphone_prefix(registry) == 'event_listeners.mp.'


def test_find_megaphone_url_raises_if_no_listeners_match():
    registry = mock.Mock()
    registry.settings = {
        'event_listeners': 'mp megaphone meeegggaaaaphoooonnnee',
        'event_listeners.mp.use': 'kinto_pusher.listeners',
        'event_listeners.mp.url': 'http://example.com/',
        'event_listeners.megaphone.use': 'kinto_fxa.listeners',
        'event_listeners.megaphone.url': 'http://example.com/',
        'event_listeners.meeegggaaaaphoooonnnee.use': 'kinto_portier.listeners',
        'event_listeners.meeegggaaaaphoooonnnee.url': 'http://example.com/',
    }

    with pytest.raises(ConfigurationError):
        kinto_megaphone.find_megaphone_prefix(registry)
