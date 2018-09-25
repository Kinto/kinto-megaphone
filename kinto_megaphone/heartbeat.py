class MegaphoneHeartbeat(object):
    def __init__(self, client):
        self.client = client

    def __call__(self, _request):
        return self.client.heartbeat()
