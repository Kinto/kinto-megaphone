import mock
import pytest
import webtest

import kinto.core
from kinto.core import events
from kinto.core.testing import DummyRequest
from pyramid.config import Configurator

from kinto_megaphone.listeners import load_from_config, CollectionTimestamp
from kinto_megaphone.megaphone import BearerAuth

def get_request_class(prefix):

    class PrefixedRequestClass(webtest.app.TestRequest):

        @classmethod
        def blank(cls, path, *args, **kwargs):
            path = '/%s%s' % (prefix, path)
            return webtest.app.TestRequest.blank(path, *args, **kwargs)

    return PrefixedRequestClass


@pytest.fixture
def megaphone_settings():
    return {
        'event_listeners': 'mp',
        'event_listeners.mp.use' : 'kinto_megaphone.listeners',
        'event_listeners.mp.api_key': 'token',
        'event_listeners.mp.url': 'http://megaphone.example.com',
        'event_listeners.mp.broadcaster_id': 'bcast',
        'bucket_create_principals': 'system.Everyone',
        'collection_create_principals': 'system.Everyone',
    }


@pytest.fixture
def kinto_app(megaphone_settings):
    api_prefix = "v1"

    settings = {**kinto.core.DEFAULT_SETTINGS}
    settings.update(kinto.DEFAULT_SETTINGS)
    settings.update(megaphone_settings)

    config = Configurator(settings=settings)
    kinto.core.initialize(config, version='0.0.1')
    config.scan("kinto.views")

    wsgi_app = config.make_wsgi_app()
    app = webtest.TestApp(wsgi_app)
    app.RequestClass = get_request_class(api_prefix)
    return app


def test_kinto_megaphone_complains_about_missing_key():
    settings = megaphone_settings()
    del settings['event_listeners.mp.api_key']
    config = Configurator(settings=settings)
    with pytest.raises(TypeError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    assert excinfo.value.args[0] == "Megaphone API key must be provided for event_listeners.mp."

def test_kinto_megaphone_complains_about_missing_url():
    settings = megaphone_settings()
    del settings['event_listeners.mp.url']
    config = Configurator(settings=settings)
    with pytest.raises(TypeError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    assert excinfo.value.args[0] == "Megaphone URL must be provided for event_listeners.mp."


def test_kinto_megaphone_complains_about_missing_broadcaster_id():
    settings = megaphone_settings()
    del settings['event_listeners.mp.broadcaster_id']
    config = Configurator(settings=settings)
    with pytest.raises(TypeError) as excinfo:
        load_from_config(config, 'event_listeners.mp.')
    assert excinfo.value.args[0] == "Megaphone broadcaster_id must be provided for event_listeners.mp."

def test_kinto_listener_puts_version():
    client = mock.Mock()
    listener = CollectionTimestamp(client, 'broadcaster')
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
    request.registry.storage.collection_timestamp.return_value = 125
    event = events.ResourceChanged(payload, single_record, request)

    listener(event)
    client.send_version.assert_called_with('broadcaster', 'food_french', '"125"')


def test_kinto_listener_ignores_reads():
    client = mock.Mock()
    listener = CollectionTimestamp(client, 'broadcaster')
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
        {'id': 'abcd'}
    ]
    request = DummyRequest()
    event = events.ResourceRead(payload, single_record, request)

    listener(event)
    assert not client.send_version.called


def test_kinto_listener_ignores_writes_not_on_records():
    client = mock.Mock()
    listener = CollectionTimestamp(client, 'broadcaster')
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