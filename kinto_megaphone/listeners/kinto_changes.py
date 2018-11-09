import logging

from pyramid.settings import aslist

from .. import megaphone, validate_config
from . import collection_timestamp

DEFAULT_SETTINGS = {}

logger = logging.getLogger(__name__)


class KintoChangesListener(collection_timestamp.CollectionTimestampListener):
    """An event listener that's specialized for handling kinto-changes feeds.

    We have a plan to allow customizing event listeners to listen for
    updates on certain buckets, collections, or records. However, we
    don't have a plan to allow filtering out impacted records from events.

    This listener understands the structure of the kinto-changes
    collection and lets us do filtering on records to only push
    timestamps when certain monitored collections change.

    """
    def __init__(self, client, broadcaster_id, resources):
        super().__init__(client, broadcaster_id)
        self.resources = resources

    def filter_records(self, impacted_records):
        return impacted_records

    def __call__(self, event):
        if event.payload['resource_name'] != 'record':
            logger.debug("Resource name did not match. Was: {}".format(
                event.payload['resource_name']))
            return

        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']
        if bucket_id != 'monitor' or collection_id != 'changes':
            logger.debug("Event was not for monitor/changes; discarding")
            return

        matching_records = self.filter_records(event.impacted_records)
        if not matching_records:
            logger.debug("No records matched; dropping event")
            return

        filtered_event = type(event)(event.payload, matching_records, event.request)

        return super().__call__(filtered_event)



def load_from_config(config, prefix):
    mp_config = validate_config(config, prefix)

    settings = config.get_settings()
    if prefix + "match_kinto_changes" not in settings:
        raise ConfigurationError("Resources to filter must be provided to kinto_changes using match_kinto_changes")
    resources = aslist(settings[prefix + "match_kinto_changes"])

    client = megaphone.Megaphone(mp_config.url, mp_config.api_key)
    return KintoChangesListener(client, mp_config.broadcaster_id, resources)
