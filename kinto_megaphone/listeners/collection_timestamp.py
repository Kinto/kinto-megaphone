import logging

from kinto.core.listeners import ListenerBase
from .. import megaphone, validate_config

DEFAULT_SETTINGS = {}

logger = logging.getLogger(__name__)


class CollectionTimestampListener(ListenerBase):
    """An event listener that pushes all collection timestamps to Megaphone.

    This is a good model of a "default" kinto_megaphone event
    listener. Every time the etag on somebucket/somecollection
    changes, it pushes that to Megaphone as
    broadcaster_id/somebucket_somecollection.

    There's no options to configure this to only notify for certain
    buckets or collections; the plan is to use Kinto's event filtering
    if you want that. See:

    https://kinto.readthedocs.io/en/stable/tutorials/notifications-custom.html
    https://github.com/Kinto/kinto/pull/1499

    """
    def __init__(self, client, broadcaster_id):
        self.client = client
        self.broadcaster_id = broadcaster_id

    def __call__(self, event):
        if event.payload['resource_name'] != 'record':
            logger.debug("Resource name did not match. Was: {}".format(
                event.payload['resource_name']))
            return

        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']
        timestamp = event.payload['timestamp']
        etag = '"{}"'.format(timestamp)
        service_id = '{}_{}'.format(bucket_id, collection_id)
        logger.info("Sending version: {}, {}".format(self.broadcaster_id, service_id))
        self.client.send_version(self.broadcaster_id,
                                 service_id,
                                 etag)


def load_from_config(config, prefix):
    mp_config = validate_config(config, prefix)
    client = megaphone.Megaphone(mp_config.url, mp_config.api_key)
    return CollectionTimestampListener(client, mp_config.broadcaster_id)
