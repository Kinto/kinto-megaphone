kinto-megaphone
===============

|travis| |master-coverage|

.. |travis| image:: https://travis-ci.org/glasserc/kinto-megaphone.svg?branch=master
    :target: https://travis-ci.org/glasserc/kinto-megaphone

.. |master-coverage| image::
    https://coveralls.io/repos/glasserc/kinto-megaphone/badge.png?branch=master
    :alt: Coverage
    :target: https://coveralls.io/r/glasserc/kinto-megaphone

Send global broadcast messages to Megaphone on changes.

* `Megaphone <https://github.com/mozilla-services/megaphone/>`_
* `Kinto documentation <http://kinto.readthedocs.io/en/latest/>`_
* `Issue tracker <https://github.com/glasserc/kinto-megaphone/issues>`_


Installation
------------

Install the Python package:

::

    pip install kinto-megaphone


Add it to kinto.includes::

    kinto.includes = kinto_megaphone

Then, you'll want to add a listener.

Listeners
---------

Listeners respond to events. kinto-megaphone listeners generally send updates to megaphone.

Add a listener using configuration like::

  kinto.event_listeners = mp
  kinto.event_listeners.mp.use = kinto_megaphone.listeners.collection_timestamp

Every kinto-megaphone listener also needs the following settings (with real values)::

  kinto.event_listeners.mp.api_key = foobar
  kinto.event_listeners.mp.url = http://megaphone.example.com/
  kinto.event_listeners.mp.broadcaster_id = remote-settings

Some listeners have additional configuration values, which will be documented below.

CollectionTimestampListener
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "default" kinto-megaphone listener is called
CollectionTimestampListener and it notifies megaphone with the new
collection timestamp every time it changes. If talking to megaphone
fails, it will abort the request (including rollback the changes made
in the request).

``CollectionTimestampListener`` is located in ``kinto_megaphone.listeners.collection_timestamp``.

``CollectionTimestampListener`` doesn't require any additional configuration outside the usual values mentioned above.

KintoChangesListener
~~~~~~~~~~~~~~~~~~~~

This listener is specialized to process events to a kinto-changes
feed. It only listens to events that correspond to records in the
``/buckets/monitor/collections/changes`` collection. Like the
``CollectionTimestampListener``, if the monitor/changes collection
timestamp would change, it sends an update to Megaphone for the
``monitor_changes`` service. However, unlike
`CollectionTimestampListener``, it has the ability to disregard
certain buckets or collections that are being monitored by
kinto-changes. This can be useful if you want to monitor many
collections but don't want all of them to trigger Megaphone updates.

This is a little bit of a hack but goes a bit further than e.g. the
filtering provided already in
https://kinto.readthedocs.io/en/stable/tutorials/notifications-custom.html
or the filtering proposed in https://github.com/Kinto/kinto/pull/1499.

You may want to set up both the ``KintoChangesListener`` and the
``CollectionTimestampListener``, but have the
``CollectionTimestampListener`` not listen on the
``/buckets/monitor/collections/changes`` collection. Unfortunately,
this will have to wait until Kinto/kinto#1499 lands.

``KintoChangesListener`` can be found at ``kinto_megaphone.listeners.kinto_changes``.

In addition to the global Megaphone settings, the
``KintoChangesListener`` requires a ``match_kinto_changes`` parameter
which represents buckets and collections whose presence in the
monitor-changes collection should trigger a Megaphone update. It
should be a list of Kinto URIs, such as::

  kinto.event_listeners.mp.match_kinto_changes = /buckets/main /buckets/blocklists /buckets/gfx

The name ``match_kinto_changes`` is kind of stupid but it was chosen
not to interfere with any names that might get used by
Kinto/kinto#1499.
