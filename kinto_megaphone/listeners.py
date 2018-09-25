from kinto.core.listeners import ListenerBase
from . import megaphone, validate_config

DEFAULT_SETTINGS = {}


class CollectionTimestampListener(ListenerBase):
    """An event listener that pushes all collection timestamps to Megaphone."""
    def __init__(self, client, broadcaster_id):
        self.client = client
        self.broadcaster_id = broadcaster_id

    def __call__(self, event):
        if event.payload['resource_name'] != 'record':
            return

        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']
        timestamp = event.payload['timestamp']
        etag = '"{}"'.format(timestamp)
        self.client.send_version(self.broadcaster_id,
                                 '{}_{}'.format(bucket_id, collection_id),
                                 etag)


def load_from_config(config, prefix):
    mp_config = validate_config(config, prefix)
    client = megaphone.Megaphone(mp_config.url, mp_config.api_key)
    return CollectionTimestampListener(client, mp_config.broadcaster_id)
