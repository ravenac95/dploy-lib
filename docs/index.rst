dploy-lib: dploy's shared library
=================================

dploy-lib is a shared library used throughout the dploy system. It provides a
standard library to facilitate a more coherent design between dploy's various
components.

Wait, what is dploy?
--------------------

dploy is an application deployment system that is meant to be similar to
systems like heroku. It utilizes many similar technologies as heroku but allows
for customization at various points in the stack. dploy was designed for Blue
Water Ads, by `Reuven V. Gonzales <https://github.com/ravenac95>`_. Many
components of the dploy stack are provided as open sourced projects on github.


Building Services
-----------------

One of the primary functions this library serves is to aid in the creation of
new dploy services. Read more here to learn how to build new services.

.. toctree::
    :maxdepth: 2

    services/intro
    services/servers

ZeroMQ Transport Wrapper
------------------------

dploy-lib provides a simple wrapper for zeromq. It provides some convenience
methods and functions, but also defines a standard messaging envelope for use
in dploy applications.

.. toctree::
    :maxdepth: 2

    transport/intro

API
---

.. toctree::
    :maxdepth: 2

    api/services


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

