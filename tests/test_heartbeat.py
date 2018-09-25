import mock
from kinto_megaphone import heartbeat


@mock.patch('kinto_megaphone.megaphone.Megaphone')
def test_heartbeat_calls_heartbeat(megaphone):
    h = heartbeat.MegaphoneHeartbeat(megaphone)

    megaphone.heartbeat.return_value = True

    assert h(None)


@mock.patch('kinto_megaphone.megaphone.Megaphone')
def test_heartbeat_understands_failure(megaphone):
    h = heartbeat.MegaphoneHeartbeat(megaphone)

    megaphone.heartbeat.return_value = False

    assert h(None) is False
