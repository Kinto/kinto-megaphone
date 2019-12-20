import logging

from pyramid.config import ConfigurationError
import pyramid.events
from pyramid.settings import aslist

from kinto.core import utils
from kinto.core.listeners import ListenerBase
from kinto_changes import MONITOR_BUCKET, CHANGES_COLLECTION
from . import megaphone, validate_config

DEFAULT_SETTINGS = {}

logger = logging.getLogger(__name__)


class KintoChangesListener(ListenerBase):
    """An event listener that's specialized for handling kinto-changes feeds.

    We have a plan to allow customizing event listeners to listen for
    updates on certain buckets, collections, or records. However, we
    don't have a plan to allow filtering out impacted records from events.

    This listener understands the structure of the kinto-changes
    collection and lets us do filtering on records to only push
    timestamps when certain monitored collections change.

    """
    def __init__(self, client, broadcaster_id, raw_resources, resources=None):
        self.client = client
        self.broadcaster_id = broadcaster_id
        self.raw_resources = raw_resources
        # Used for testing, to pass parsed resources without having to
        # scan views etc.
        if resources:
            self.resources = resources

    def _convert_resources(self, event):
        self.resources = [
            utils.view_lookup_registry(event.app.registry, r)
            for r in self.raw_resources
        ]

    def filter_records(self, impacted_records):
        ret = []
        for delta in impacted_records:
            if 'new' not in delta:
                continue  # skip deletes
            record = delta['new']
            record_bucket = record['bucket']
            record_collection = record['collection']
            for (resource_name, matchdict) in self.resources:
                if resource_name == 'bucket':
                    resource_bucket = matchdict['id']
                else:
                    resource_bucket = matchdict.get('bucket_id')

                if resource_name == 'collection':
                    resource_collection = matchdict['id']
                else:
                    resource_collection = matchdict.get('collection_id')

                if resource_bucket and resource_bucket != record_bucket:
                    continue

                if resource_collection and resource_collection != record_collection:
                    continue

                ret.append(record)

        return ret

    def __call__(self, event):
        if event.payload['resource_name'] != 'record':
            logger.debug("Resource name did not match. Was: {}".format(
                event.payload['resource_name']))
            return

        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']
        if bucket_id != MONITOR_BUCKET or collection_id != CHANGES_COLLECTION:
            logger.debug("Event was not for monitor/changes; discarding")
            return

        matching_records = self.filter_records(event.impacted_records)
        if not matching_records:
            logger.debug("No records matched; dropping event")
            return

        # Timestamp comes from "changes" object (ie. first impacted record).
        timestamp = matching_records[0]["last_modified"]
        etag = '"{}"'.format(timestamp)

        return self.send_notification(bucket_id, collection_id, etag)

    def send_notification(self, bucket_id, collection_id, version):
        service_id = '{}_{}'.format(bucket_id, collection_id)
        logger.info("Sending version: {}, {}".format(self.broadcaster_id, service_id))
        self.client.send_version(self.broadcaster_id, service_id, version)


def load_from_config(config, prefix):
    mp_config = validate_config(config, prefix)

    settings = config.get_settings()
    if prefix + "match_kinto_changes" not in settings:
        ERROR_MSG = ("Resources to filter must be provided to kinto_changes "
                     "using match_kinto_changes")
        raise ConfigurationError(ERROR_MSG)
    resources = aslist(settings[prefix + "match_kinto_changes"])

    client = megaphone.Megaphone(mp_config.url, mp_config.api_key)
    listener = KintoChangesListener(client, mp_config.broadcaster_id, resources)
    config.add_subscriber(listener._convert_resources,
                          pyramid.events.ApplicationCreated)
    return listener
