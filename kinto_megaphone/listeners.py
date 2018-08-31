from kinto.core.events import ResourceChanged
from kinto.core.listeners import ListenerBase
from . import megaphone

DEFAULT_SETTINGS = {}

class CollectionTimestamp(ListenerBase):
    """An event listener that pushes all collection timestamps to Megaphone."""
    def __init__(self, client, broadcaster_id):
        self.client = client
        self.broadcaster_id = broadcaster_id

    def __call__(self, event):
        if not isinstance(event, ResourceChanged):
            return

        if event.payload['resource_name'] != 'record':
            return

        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']
        storage = event.request.registry.storage
        parent_id = '/buckets/{}/collections/{}/records'.format(bucket_id, collection_id)
        etag = storage.collection_timestamp('record', parent_id)
        self.client.send_version(self.broadcaster_id,
                                 '{}_{}'.format(bucket_id, collection_id),
                                 '"{}"'.format(etag))


def load_from_config(config, prefix):
    settings = config.get_settings()

    if prefix + 'api_key' not in settings:
        raise TypeError("Megaphone API key must be provided for {}".format(prefix))
    api_key = settings[prefix+'api_key']

    if prefix + 'url' not in settings:
        raise TypeError("Megaphone URL must be provided for {}".format(prefix))
    url = settings[prefix + 'url']

    if prefix + 'broadcaster_id' not in settings:
        raise TypeError("Megaphone broadcaster_id must be provided for {}".format(prefix))
    broadcaster_id = settings[prefix + 'broadcaster_id']

    client = megaphone.Megaphone(url, api_key)
    return CollectionTimestamp(client, broadcaster_id)
