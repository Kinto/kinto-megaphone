"""
A thin client for the Megaphone service.
"""

import requests.auth


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __eq__(self, rhs):
        return self.token == rhs.token

    def __call__(self, r):
        r.headers['Authorization'] = "Bearer {}".format(self.token)
        return r


class Megaphone(object):
    def __init__(self, url, api_key):
        self.url = url.rstrip('/')
        self.auth = api_key and BearerAuth(api_key)

    def _assert_auth(self):
        if not self.auth:
            raise ValueError("cannot invoke this Megaphone API without authentication")

    def send_version(self, broadcaster_id, channel_id, version):
        self._assert_auth()

        url = '{}/v1/broadcasts/{}/{}'.format(self.url, broadcaster_id, channel_id)
        resp = requests.put(url, auth=self.auth, data=version)
        resp.raise_for_status()

    def heartbeat(self):
        url = '{}/__heartbeat__'.format(self.url)
        resp = requests.get(url)
        return resp.status_code == 200
