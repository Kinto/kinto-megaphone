import mock
import pytest
from kinto.core import events
from kinto.core.testing import DummyRequest
from pyramid.config import Configurator, ConfigurationError

from kinto_megaphone.listeners import (
    load_from_config,
    KintoChangesListener,
    )
from kinto_megaphone.megaphone import BearerAuth


@pytest.fixture
def match_buckets_a_resource():
    return [('bucket', {'id': 'a'})]


@pytest.fixture
def match_collection_z1_resource():
    return [('collection', {'id': 'z1', 'bucket_id': 'z'})]


PAYLOAD = {
    'timestamp': '123',
    'action': events.ACTIONS.CREATE,
    'uri': 'abcd',
    'user_id': 'accounts:eglassercamp@mozilla.com',
    'resource_name': 'record',
    'bucket_id': 'monitor',
    'collection_id': 'changes',
    'id': 'blahblah',
}


def changes_record(bucket_id, collection_id):
    """Utility function to gin up something that is kind of like a kinto-changes record."""
    return {
        'id': 'abcd',
        'last_modified': 123,
        'bucket': bucket_id,
        'collection': collection_id,
        'host': 'http://localhost',
    }


def test_kinto_megaphone_complains_about_missing_key(kinto_changes_settings):
    del kinto_changes_settings['event_listeners.mp.api_key']
    config = Configurator(settings=kinto_changes_settings)
    with pytest.raises(ConfigurationError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    assert excinfo.value.args[0] == "Megaphone API key must be provided for event_listeners.mp."


def test_kinto_megaphone_complains_about_missing_url(kinto_changes_settings):
    del kinto_changes_settings['event_listeners.mp.url']
    config = Configurator(settings=kinto_changes_settings)
    with pytest.raises(ConfigurationError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    assert excinfo.value.args[0] == "Megaphone URL must be provided for event_listeners.mp."


def test_kinto_megaphone_complains_about_missing_broadcaster_id(kinto_changes_settings):
    del kinto_changes_settings['event_listeners.mp.broadcaster_id']
    config = Configurator(settings=kinto_changes_settings)
    with pytest.raises(ConfigurationError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    error_msg = "Megaphone broadcaster_id must be provided for event_listeners.mp."
    assert excinfo.value.args[0] == error_msg


def test_kinto_changes_complains_about_missing_config_param(kinto_changes_settings):
    del kinto_changes_settings['event_listeners.mp.match_kinto_changes']
    config = Configurator(settings=kinto_changes_settings)
    with pytest.raises(ConfigurationError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    ERROR_MSG = "Resources to filter must be provided to kinto_changes" \
        " using match_kinto_changes"
    assert excinfo.value.args[0] == ERROR_MSG


def test_kinto_changes_ignores_not_monitor_changes(match_buckets_a_resource):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], match_buckets_a_resource)
    payload = {
        **PAYLOAD,
        'bucket_id': 'food',
        'collection_id': 'french',
    }
    single_record = [
        {'new': {'id': 'abcd'}}
    ]
    request = DummyRequest()
    event = events.ResourceChanged(payload, single_record, request)

    listener(event)
    assert not client.send_version.called


def test_kcl_ignores_writes_not_on_records(match_buckets_a_resource):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], match_buckets_a_resource)
    payload = {
        **PAYLOAD,
        'resource_name': 'collection',
    }
    single_record = [
        {'new': changes_record('a', 'c')}
    ]
    request = DummyRequest()
    event = events.ResourceChanged(payload, single_record, request)

    listener(event)
    assert not client.send_version.called


def test_kcl_ignores_missing_new(match_buckets_a_resource):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], match_buckets_a_resource)
    single_record = [
        {'old': changes_record('a', 'c')},
    ]
    request = DummyRequest()
    event = events.ResourceChanged(PAYLOAD, single_record, request)

    listener(event)
    assert not client.send_version.called


def test_kcl_drops_events_with_no_matching_records(match_buckets_a_resource):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [], match_buckets_a_resource)
    single_record = [
        {'new': changes_record('b', 'c')},
    ]
    request = DummyRequest()
    event = events.ResourceChanged(PAYLOAD, single_record, request)

    listener(event)
    assert not client.send_version.called


def test_kcl_posts_on_matching_records(match_buckets_a_resource):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [],
                                    match_buckets_a_resource)
    single_record = [
        {'new': changes_record('a', 'c')},
    ]
    request = DummyRequest()
    event = events.ResourceChanged(PAYLOAD, single_record, request)

    listener(event)
    client.send_version.assert_called_with('broadcaster', 'monitor_changes', '"123"')


def test_kcl_calls_with_some_matching_records(match_buckets_a_resource):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [],
                                    match_buckets_a_resource)
    two_records = [
        {'new': changes_record('b', 'c')},
        {'new': changes_record('a', 'c')},
    ]
    request = DummyRequest()
    event = events.ResourceChanged(PAYLOAD, two_records, request)

    listener(event)
    client.send_version.assert_called_with('broadcaster', 'monitor_changes', '"123"')


def test_kcl_can_match_in_collections(match_collection_z1_resource):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [],
                                    match_collection_z1_resource)
    one_record = [
        {'new': changes_record('z', 'z1')},
    ]
    request = DummyRequest()
    event = events.ResourceChanged(PAYLOAD, one_record, request)

    listener(event)
    client.send_version.assert_called_with('broadcaster', 'monitor_changes', '"123"')


def test_kcl_can_fail_to_match_in_collections(match_collection_z1_resource):
    client = mock.Mock()
    listener = KintoChangesListener(client, 'broadcaster', [],
                                    match_collection_z1_resource)
    one_record = [
        {'new': changes_record('z', 'z2')},
    ]
    request = DummyRequest()
    event = events.ResourceChanged(PAYLOAD, one_record, request)

    listener(event)
    assert not client.send_version.called


@mock.patch('kinto_megaphone.megaphone.requests')
def test_kinto_app_puts_version(requests, kinto_app):
    app = kinto_app
    app.put_json('/buckets/a', {})
    app.put_json('/buckets/a/collections/a_1', {})
    resp = app.put_json('/buckets/a/collections/a_1/records/a_1_2', {})
    records_etag = resp.headers['ETag']

    resp = app.get('/buckets/a/collections/a_1/records')
    collection_etag = resp.headers['ETag']
    assert records_etag == collection_etag

    assert requests.put.call_count == 1
    monitor_changes_endpoint = 'http://megaphone.example.com/v1/broadcasts/bcast/monitor_changes'
    requests.put.assert_called_with(monitor_changes_endpoint,
                                    auth=BearerAuth('token'),
                                    data=records_etag)


@mock.patch('kinto_megaphone.megaphone.requests')
def test_kinto_app_ignores_other_kinto_changes_version(requests, kinto_app):
    app = kinto_app
    app.put_json('/buckets/some-random-bucket', {})
    app.put_json('/buckets/some-random-bucket/collections/a_1', {})
    app.put_json('/buckets/some-random-bucket/collections/a_1/records/a_1_2', {})

    assert not requests.put.called
