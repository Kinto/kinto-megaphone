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

* `Kinto documentation <http://kinto.readthedocs.io/en/latest/>`_
* `Issue tracker <https://github.com/glasserc/kinto-megaphone/issues>`_


Installation
------------

Install the Python package:

::

    pip install kinto-megaphone


Include the package in the project configuration:

::

    kinto.includes = kinto_megaphone



Configuration
-------------

Fill those settings with the values obtained during the application registration:

::

    # kinto.megaphone.whatever = foobar
