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


Then, you'll want to add a listener. kinto-megaphone only offers one
kind of listener right now, but that could change later.

Add it using configuration like::

  kinto.event_listeners = mp
  kinto.event_listeners.mp.use = kinto_megaphone.listeners

Every listener also needs the following settings (with real values)::

  kinto.event_listeners.mp.api_key = foobar
  kinto.event_listeners.mp.url = http://megaphone.example.com/
  kinto.event_listeners.mp.broadcaster_id = remote-settings
