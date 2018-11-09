import pytest
import webtest

import kinto.core
from pyramid.config import Configurator


def get_request_class(prefix):

    class PrefixedRequestClass(webtest.app.TestRequest):
        @classmethod
        def blank(cls, path, *args, **kwargs):
            path = '/%s%s' % (prefix, path)
            return webtest.app.TestRequest.blank(path, *args, **kwargs)

    return PrefixedRequestClass


@pytest.fixture
def collection_timestamp_settings():
    return {
        'project_name': 'kinto megaphone test',
        'event_listeners': 'mp',
        'event_listeners.mp.use': 'kinto_megaphone.listeners.collection_timestamp',
        'event_listeners.mp.api_key': 'token',
        'event_listeners.mp.url': 'http://megaphone.example.com',
        'event_listeners.mp.broadcaster_id': 'bcast',
        'bucket_create_principals': 'system.Everyone',
        'collection_create_principals': 'system.Everyone',
        'includes': 'kinto_megaphone',
    }


@pytest.fixture
def kinto_changes_settings():
    return {
        'project_name': 'kinto megaphone test',
        'event_listeners': 'mp',
        'event_listeners.mp.use': 'kinto_megaphone.listeners.kinto_changes',
        'event_listeners.mp.api_key': 'token',
        'event_listeners.mp.url': 'http://megaphone.example.com',
        'event_listeners.mp.broadcaster_id': 'bcast',
        'event_listeners.mp.match_kinto_changes': '/buckets/a /buckets/z/collections/z1',
        'bucket_create_principals': 'system.Everyone',
        'collection_create_principals': 'system.Everyone',
        'includes': 'kinto_megaphone kinto_changes',
        'changes.resources': '/buckets/a /buckets/some-random-bucket /buckets/z/collections/z1 /buckets/z/collections/z2',
    }


@pytest.fixture
def kinto_app(collection_timestamp_settings):
    api_prefix = "v1"

    settings = {**kinto.core.DEFAULT_SETTINGS}
    settings.update(kinto.DEFAULT_SETTINGS)
    settings.update(collection_timestamp_settings)

    config = Configurator(settings=settings)

    # FIXME: https://github.com/Kinto/kinto-changes/issues/49
    config.registry.command = 'start'

    kinto.core.initialize(config, version='0.0.1')
    config.scan("kinto.views")

    wsgi_app = config.make_wsgi_app()
    app = webtest.TestApp(wsgi_app)
    app.RequestClass = get_request_class(api_prefix)
    return app
