import mock


@mock.patch('kinto_megaphone.megaphone.requests')
def test_kinto_app_adds_heartbeat(requests, kinto_app):
    requests.get.return_value.status_code = 200

    resp = kinto_app.get('/__heartbeat__')

    assert requests.get.call_count == 1
    requests.get.assert_called_with('http://megaphone.example.com/__heartbeat__')

    assert 'megaphone' in resp.json
    assert resp.json['megaphone']


def test_kinto_app_adds_capability(kinto_app):
    resp = kinto_app.get('/')
    capabilities = resp.json['capabilities']
    assert 'megaphone' in capabilities
    megaphone = capabilities['megaphone']
    assert 'broadcast' in megaphone['description'].lower()
    assert megaphone['url'] == 'https://github.com/Kinto/kinto-megaphone'
