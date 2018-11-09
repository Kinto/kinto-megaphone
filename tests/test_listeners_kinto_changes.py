import mock
import pytest
import kinto.core
from kinto.core import events
from kinto.core.testing import DummyRequest
from pyramid.config import Configurator, ConfigurationError

from kinto_megaphone.listeners.kinto_changes import load_from_config, KintoChangesListener
from kinto_megaphone.megaphone import BearerAuth
import conftest


@pytest.fixture
def kinto_changes_listener_match_buckets_a():
    return [('bucket', {'id': 'a'})]

def test_kinto_changes_complains_about_missing_config_param(kinto_changes_settings):
    del kinto_changes_settings['event_listeners.mp.match_kinto_changes']
    config = Configurator(settings=kinto_changes_settings)
    with pytest.raises(ConfigurationError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    assert excinfo.value.args[0] == "Resources to filter must be provided to kinto_changes using match_kinto_changes"


def test_kinto_changes_ignores_not_monitor_changes(kinto_changes_listener_match_buckets_a):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], kinto_changes_listener_match_buckets_a)
    payload = {
        'timestamp': '123',
        'action': events.ACTIONS.CREATE,
        'uri': 'abcd',
        'user_id': 'accounts:eglassercamp@mozilla.com',
        'resource_name': 'record',
        'bucket_id': 'food',
        'collection_id': 'french',
        'id': 'blahblah',
    }
    single_record = [
        {'new': {'id': 'abcd'}}
    ]
    request = DummyRequest()
    event = events.ResourceChanged(payload, single_record, request)

    listener(event)
    assert not client.send_version.called


def test_kinto_changes_listener_ignores_writes_not_on_records(kinto_changes_listener_match_buckets_a):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], kinto_changes_listener_match_buckets_a)
    payload = {
        'timestamp': '123',
        'action': events.ACTIONS.CREATE,
        'uri': 'abcd',
        'user_id': 'accounts:eglassercamp@mozilla.com',
        'resource_name': 'collection',
        'bucket_id': 'monitor',
        'collection_id': 'changes',
        'id': 'french',
    }
    single_record = [
        {'new': {'id': 'abcd', 'last_modified': 123, 'bucket': 'a', 'collection': 'c', 'host': 'http://localhost'}}
    ]
    request = DummyRequest()
    event = events.ResourceChanged(payload, single_record, request)

    listener(event)
    assert not client.send_version.called


def test_kinto_changes_listener_drops_events_with_no_matching_records(kinto_changes_listener_match_buckets_a):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], kinto_changes_listener_match_buckets_a)
    payload = {
        'timestamp': '123',
        'action': events.ACTIONS.CREATE,
        'uri': 'abcd',
        'user_id': 'accounts:eglassercamp@mozilla.com',
        'resource_name': 'record',
        'bucket_id': 'monitor',
        'collection_id': 'changes',
        'id': 'french',
    }
    single_record = [
        {'new': {'id': 'abcd', 'last_modified': 123, 'bucket': 'b', 'collection': 'c', 'host': 'http://localhost'}}
    ]
    request = DummyRequest()
    event = events.ResourceChanged(payload, single_record, request)

    listener(event)
    assert not client.send_version.called


def test_kinto_changes_listener_posts_on_matching_records(kinto_changes_listener_match_buckets_a):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], kinto_changes_listener_match_buckets_a)
    payload = {
        'timestamp': '123',
        'action': events.ACTIONS.CREATE,
        'uri': 'abcd',
        'user_id': 'accounts:eglassercamp@mozilla.com',
        'resource_name': 'record',
        'bucket_id': 'monitor',
        'collection_id': 'changes',
        'id': 'french',
    }
    single_record = [
        {'new': {'id': 'abcd', 'last_modified': 123, 'bucket': 'a', 'collection': 'c', 'host': 'http://localhost'}}
    ]
    request = DummyRequest()
    event = events.ResourceChanged(payload, single_record, request)

    listener(event)
    client.send_version.assert_called_with('broadcaster', 'monitor_changes', '"123"')


def test_kinto_changes_listener_calls_with_some_matching_records(kinto_changes_listener_match_buckets_a):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], kinto_changes_listener_match_buckets_a)
    payload = {
        'timestamp': '123',
        'action': events.ACTIONS.CREATE,
        'uri': 'abcd',
        'user_id': 'accounts:eglassercamp@mozilla.com',
        'resource_name': 'record',
        'bucket_id': 'monitor',
        'collection_id': 'changes',
        'id': 'french',
    }
    two_records = [
        {'new': {'id': 'abcd', 'last_modified': 123, 'bucket': 'b', 'collection': 'c', 'host': 'http://localhost'}},
        {'new': {'id': 'abcd', 'last_modified': 123, 'bucket': 'a', 'collection': 'c', 'host': 'http://localhost'}}
    ]
    request = DummyRequest()
    event = events.ResourceChanged(payload, two_records, request)

    listener(event)
    client.send_version.assert_called_with('broadcaster', 'monitor_changes', '"123"')


@mock.patch('kinto_megaphone.megaphone.requests')
def test_kinto_app_puts_version(requests, kinto_changes_settings):
    app = conftest.kinto_app(kinto_changes_settings)
    app.put_json('/buckets/a', {})
    app.put_json('/buckets/a/collections/a_1', {})
    resp = app.put_json('/buckets/a/collections/a_1/records/a_1_2', {})
    records_etag = resp.headers['ETag']

    resp = app.get('/buckets/a/collections/a_1/records')
    collection_etag = resp.headers['ETag']
    assert records_etag == collection_etag

    assert requests.put.call_count == 1
    requests.put.assert_called_with('http://megaphone.example.com/v1/broadcasts/bcast/monitor_changes',
                                    auth=BearerAuth('token'),
                                    data=records_etag)

@mock.patch('kinto_megaphone.megaphone.requests')
def test_kinto_app_ignores_other_kinto_changes_version(requests, kinto_changes_settings):
    app = conftest.kinto_app(kinto_changes_settings)
    app.put_json('/buckets/some-random-bucket', {})
    app.put_json('/buckets/some-random-bucket/collections/a_1', {})
    resp = app.put_json('/buckets/some-random-bucket/collections/a_1/records/a_1_2', {})

    assert not requests.put.called
