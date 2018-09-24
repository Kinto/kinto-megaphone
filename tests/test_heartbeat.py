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
