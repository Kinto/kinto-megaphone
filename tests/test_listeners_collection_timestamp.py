import mock
import pytest
from kinto.core import events
from kinto.core.testing import DummyRequest
from pyramid.config import Configurator, ConfigurationError

from kinto_megaphone.listeners.collection_timestamp import (
    load_from_config,
    CollectionTimestampListener,
)
from kinto_megaphone.megaphone import BearerAuth


def test_kinto_megaphone_complains_about_missing_key(collection_timestamp_settings):
    del collection_timestamp_settings['event_listeners.mp.api_key']
    config = Configurator(settings=collection_timestamp_settings)
    with pytest.raises(ConfigurationError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    assert excinfo.value.args[0] == "Megaphone API key must be provided for event_listeners.mp."


def test_kinto_megaphone_complains_about_missing_url(collection_timestamp_settings):
    del collection_timestamp_settings['event_listeners.mp.url']
    config = Configurator(settings=collection_timestamp_settings)
    with pytest.raises(ConfigurationError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    assert excinfo.value.args[0] == "Megaphone URL must be provided for event_listeners.mp."


def test_kinto_megaphone_complains_about_missing_broadcaster_id(collection_timestamp_settings):
    del collection_timestamp_settings['event_listeners.mp.broadcaster_id']
    config = Configurator(settings=collection_timestamp_settings)
    with pytest.raises(ConfigurationError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    error_msg = "Megaphone broadcaster_id must be provided for event_listeners.mp."
    assert excinfo.value.args[0] == error_msg


def test_kinto_listener_puts_version():
    client = mock.Mock()
    listener = CollectionTimestampListener(client, 'broadcaster')
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
    client.send_version.assert_called_with('broadcaster', 'food_french', '"123"')


def test_kinto_listener_ignores_writes_not_on_records():
    client = mock.Mock()
    listener = CollectionTimestampListener(client, 'broadcaster')
    payload = {
        'timestamp': '123',
        'action': events.ACTIONS.CREATE,
        'uri': 'abcd',
        'user_id': 'accounts:eglassercamp@mozilla.com',
        'resource_name': 'collection',
        'bucket_id': 'food',
        'id': 'french',
    }
    single_record = [
        {'new': {'id': 'abcd'}}
    ]
    request = DummyRequest()
    event = events.ResourceChanged(payload, single_record, request)

    listener(event)
    assert not client.send_version.called


@mock.patch('kinto_megaphone.megaphone.requests')
def test_kinto_app_puts_version(requests, kinto_app):
    kinto_app.put_json('/buckets/food', {})
    kinto_app.put_json('/buckets/food/collections/french', {})
    resp = kinto_app.put_json('/buckets/food/collections/french/records/escargot', {})
    records_etag = resp.headers['ETag']

    resp = kinto_app.get('/buckets/food/collections/french/records')
    collection_etag = resp.headers['ETag']
    assert records_etag == collection_etag

    assert requests.put.call_count == 1
    requests.put.assert_called_with('http://megaphone.example.com/v1/broadcasts/bcast/food_french',
                                    auth=BearerAuth('token'),
                                    data=records_etag)
