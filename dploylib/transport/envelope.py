# -*- coding: utf-8 -*-

"""
dploylib.transport.envelope
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines the envelope. The envelope is how all of the communication occurs
between dploy services. This does not include dploy web services. Those differ
from zeromq based services.
"""


class Envelope(object):
    """Dploy's message envelope.

    This is a standard definition so that all messages are decoded the same
    way. The envelope is as follows (for the time being)::

         -----------------------
        | id - a string or ''   |
         -----------------------
        | mimetype              |
         -----------------------
        | body                  |
         -----------------------

    .. note::

        The ``id`` portion of the envelope may seem like unnecessary data, but
        it allows the envelope to be used in pub-sub effectively.

    :param id: A string id for the envelope
    :type id: str
    :param mimetype: The mimetype for the envelope
    :type mimetype: str
    :param data: The envelope's body
    """
    @classmethod
    def new(cls, mimetype, data, id=''):
        """Create a new envelope. This is the preferred way to create a new
        envelope.

        :param mimetype: The mimetype for the envelope
        :param data: The envelope's body
        :param id: (optional) A string id for the envelope. Defaults to ''
        """
        return cls(id, mimetype, data)

    @classmethod
    def from_raw(cls, raw):
        """Creates an envelope from a tuple or list

        :param raw: Raw data for an envelope
        :type raw: tuple or list
        """

        id, mimetype, data = raw
        return cls(id, mimetype, data)

    def __init__(self, id, mimetype, data):
        self._id = id
        self._mimetype = mimetype
        self._data = data

    @property
    def id(self):
        return self._id

    @property
    def mimetype(self):
        return self._mimetype

    @property
    def data(self):
        return self._data

    def transfer_object(self):
        """This is the object to be sent over the wire. The reverse of this is
        Envelope.from_raw

        For zmq this should be an list
        """
        return [self._id, self._mimetype, self._data]
