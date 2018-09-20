import mock
import pytest
from pyramid.config import ConfigurationError

from kinto_megaphone import heartbeat


@mock.patch('kinto_megaphone.megaphone.Megaphone')
def test_heartbeat_calls_heartbeat(megaphone):
    h = heartbeat.MegaphoneHeartbeat(megaphone)

    megaphone.heartbeat.return_value = {
        "code": 200,
        "database": "ok",
        "status": "ok"
    }

    assert h(None)


@mock.patch('kinto_megaphone.megaphone.Megaphone')
def test_heartbeat_understands_failure(megaphone):
    h = heartbeat.MegaphoneHeartbeat(megaphone)

    # I've never had this response from megaphone.
    # Instead when I shut down mysql, the megaphone service just
    # hangs forever while spewing error messages about how it can't
    # access the database.
    # Maybe it's possible to get an error message like this, but I
    # don't know how.
    megaphone.heartbeat.return_value = {
        "code": 200,
        "database": "bad",
        "status": "ok"
    }

    assert h(None) is False


def test_find_megaphone_url_reads_settings():
    registry = mock.Mock()
    registry.settings = {
        'event_listeners': 'mp',
        'event_listeners.mp.use': 'kinto_megaphone.listeners',
        'event_listeners.mp.url': 'http://example.com/',
    }

    assert heartbeat.find_megaphone_url(registry) == 'http://example.com/'


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
        heartbeat.find_megaphone_url(registry)
