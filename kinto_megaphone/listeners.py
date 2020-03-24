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


def match_resource(resource, bid, cid):
    """Helper that returns True if the specified bucket id and collection id
    match the given resource.
    """
    resource_name, matchdict = resource
    resource_bucket = matchdict['id'] if resource_name == 'bucket' else matchdict['bucket_id']
    resource_collection = matchdict['id'] if resource_name == 'collection' else None

    same_bucket = resource_bucket == bid
    same_collection = resource_collection and resource_collection == cid

    if same_bucket and (resource_name == 'bucket' or same_collection):
        return True

    return False


class KintoChangesListener(ListenerBase):
    """An event listener that's specialized for handling kinto-changes feeds.

    We have a plan to allow customizing event listeners to listen for
    updates on certain buckets, collections, or records. However, we
    don't have a plan to allow filtering out impacted records from events.

    This listener understands the structure of the kinto-changes
    collection and lets us do filtering on records to only push
    timestamps when certain monitored collections change.

    """
    def __init__(
        self, client, broadcaster_id, included_resources, excluded_resources, resources=None
    ):
        self.client = client
        self.broadcaster_id = broadcaster_id
        self.included_resources_uris = included_resources
        self.included_resources = []
        self.excluded_resources_uris = excluded_resources
        self.excluded_resources = []
        # Used for testing, to pass parsed resources without having to
        # scan views etc.
        if resources:
            self.included_resources = resources

    def _convert_resources(self, event):
        """ This event listener is called on application startup.
        """
        # [('bucket', {'id': 'a'}), ('collection', {'bucket_id': 'z', 'id': 'z1'})]
        self.excluded_resources = [
            utils.view_lookup_registry(event.app.registry, r)
            for r in self.excluded_resources_uris
        ]
        self.included_resources = [
            utils.view_lookup_registry(event.app.registry, r)
            for r in self.included_resources_uris
        ]

    def filter_records(self, impacted_records):
        ret = []
        for delta in impacted_records:
            if 'new' not in delta:
                continue  # skip deletes
            record = delta['new']
            bid = record['bucket']
            cid = record['collection']

            match = (
                any(match_resource(r, bid, cid) for r in self.included_resources) and
                not any(match_resource(r, bid, cid) for r in self.excluded_resources)
            )
            if match:
                ret.append(record)

        return ret

    def __call__(self, event):
        if event.payload['resource_name'] != 'record':
            logger.debug("Resource name did not match. Was: {}".format(
                event.payload['resource_name']))
            return

        # We are only interested in ResourceChanged events on 'record'
        # in the "monitor/changes" collection. These events are forged
        # by the Kinto/kinto-changes plugin.
        bucket_id = event.payload['bucket_id']
        collection_id = event.payload['collection_id']
        if bucket_id != MONITOR_BUCKET or collection_id != CHANGES_COLLECTION:
            logger.debug("Event was not for monitor/changes; discarding")
            return

        # In Kinto/kinto-changes, we send events every time there is a record
        # change in the watched collections. In Megaphone, we don't send notifs
        # for all of them (eg. not preview).
        matching_records = self.filter_records(event.impacted_records)
        if not matching_records:
            logger.debug("No records matched; dropping event")
            return

        # In Kinto/kinto-changes, the event data contains information about
        # then changed collection(s). The `last_modified` field is the collection
        # plural timestamp.
        timestamp = max(r["last_modified"] for r in matching_records)
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
    included_resources = aslist(settings[prefix + "match_kinto_changes"])

    excluded_resources = aslist(settings.get(prefix + "except_kinto_changes", ""))

    client = megaphone.Megaphone(mp_config.url, mp_config.api_key)
    listener = KintoChangesListener(
        client, mp_config.broadcaster_id,
        included_resources, excluded_resources)
    config.add_subscriber(listener._convert_resources, pyramid.events.ApplicationCreated)
    return listener
