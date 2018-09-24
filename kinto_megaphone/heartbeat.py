class MegaphoneHeartbeat(object):
    def __init__(self, client):
        self.client = client

    def __call__(self, _request):
        data = self.client.heartbeat()
        return data['database'] == 'ok' and data['status'] == 'ok'
