import pytest
import webtest

import kinto.core
from pyramid.config import Configurator

from kinto_megaphone.listeners import load_from_config


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
    with pytest.raises(TypeError, message="Megaphone API key must be provided for mp"):
        load_from_config(settings)

def test_kinto_megaphone_complains_about_missing_url():
    settings = megaphone_settings()
    del settings['event_listeners.mp.url']
    with pytest.raises(TypeError, message="Megaphone url must be provided for mp"):
        load_from_config(settings)

def test_kinto_megaphone_complains_about_missing_broadcaster_id():
    settings = megaphone_settings()
    del settings['event_listeners.mp.broadcaster_id']
    with pytest.raises(TypeError, message="Megaphone broadcaster_id must be provided for mp"):
        load_from_config(settings)
