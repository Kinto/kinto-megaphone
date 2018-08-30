import pytest
import webtest

import kinto.core
from pyramid.config import Configurator

from kinto_megaphone import __version__ as plugin_version


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
        'megaphone.api_key': 'token',
        'megaphone.url': 'http://megaphone.example.com',
    }


@pytest.fixture
def kinto_app(megaphone_settings):
    api_prefix = "v1"

    settings = {**kinto.core.DEFAULT_SETTINGS}
    settings.update(kinto.DEFAULT_SETTINGS)
    settings['includes'] += ' kinto_megaphone'
    settings.update(megaphone_settings)

    config = Configurator(settings=settings)
    kinto.core.initialize(config, version='0.0.1')
    config.scan("kinto.views")

    wsgi_app = config.make_wsgi_app()
    app = webtest.TestApp(wsgi_app)
    app.RequestClass = get_request_class(api_prefix)
    return app


def test_kinto_megaphone_capability(kinto_app):
    resp = kinto_app.get('/')
    capabilities = resp.json['capabilities']
    assert 'megaphone' in capabilities
    expected = {
        "version": plugin_version,
        "url": "https://github.com/glasserc/kinto-megaphone",
        "description": "Send global broadcast messages to Megaphone on changes"
    }
    assert expected == capabilities['megaphone']


def test_kinto_megaphone_complains_about_missing_key():
    with pytest.raises(TypeError, message="Megaphone API key must be provided as megaphone.api_key"):
        kinto_app({"megaphone.url": "some_url"})

def test_kinto_megaphone_complains_about_missing_url():
    with pytest.raises(TypeError, message="Megaphone url must be provided as megaphone.url"):
        kinto_app({"megaphone.api_key": "api_key"})
