kinto-megaphone
===============

|travis| |master-coverage|

.. |travis| image:: https://travis-ci.org/Kinto/kinto-megaphone.svg?branch=master
    :target: https://travis-ci.org/Kinto/kinto-megaphone

.. |master-coverage| image::
    https://coveralls.io/repos/Kinto/kinto-megaphone/badge.png?branch=master
    :alt: Coverage
    :target: https://coveralls.io/r/Kinto/kinto-megaphone

Send global broadcast messages to Megaphone on changes.

* `Megaphone <https://github.com/mozilla-services/megaphone/>`_
* `Kinto documentation <http://kinto.readthedocs.io/en/latest/>`_
* `Issue tracker <https://github.com/Kinto/kinto-megaphone/issues>`_


Installation
------------

Install the Python package:

::

    pip install kinto-megaphone


Add it to kinto.includes::

    kinto.includes = kinto_megaphone

Then, you'll want to add a listener.

The kinto-megaphone listener is called ``KintoChangesListener`` and
it watches the ``monitor/changes`` collection from ``kinto-changes``.
You provide a list of resources, and when those resources are updated
in ``monitor/changes``, we notify Megaphone with the new collection
timestamp.

If talking to Megaphone fails, it will abort the request (including
rolling back the changes made in the request).

kinto-megaphone only offers this one kind of listener right
now, but that could change later.

Add it using configuration like::

  kinto.event_listeners = mp
  kinto.event_listeners.mp.use = kinto_megaphone.listeners
  kinto.event_listeners.mp.api_key = foobar
  kinto.event_listeners.mp.url = https://megaphone.example.com/
  kinto.event_listeners.mp.broadcaster_id = remote-settings
  kinto.event_listeners.mp.match_kinto_changes = /buckets/main /buckets/blocklists/collections/addons /buckets/blocklists/collections/gfx

Note that the ``match_kinto_changes`` configuration only lets you
describe resources that are tracked by kinto-changes -- you won't be
able to put e.g. groups or accounts in there.
