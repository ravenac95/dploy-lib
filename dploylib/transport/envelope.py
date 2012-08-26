# -*- coding: utf-8 -*-

"""
dploylib.transport.envelope
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines the envelope. The envelope is how all of the communication occurs
between dploy services. This does not include dploy web services. Those differ
from zeromq based services.
"""
ENVELOPE_SCHEMA = ['id', 'mimetype', 'body']
MINIMUM_ENVELOPE_LEN = len(ENVELOPE_SCHEMA)


class Envelope(object):
    """Dploy's message envelope.

    This is a standard definition so that all messages are decoded the same
    way. The envelope is as follows (for the time being)::
         -----------------------
        | any request frames    |
         -----------------------
        | empty frame if above  |
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
    def new(cls, mimetype, data, id='', request_frames=None):
        """Create a new envelope. This is the preferred way to create a new
        envelope.

        :param mimetype: The mimetype for the envelope
        :param data: The envelope's body
        :param id: (optional) A string id for the envelope. Defaults to ''
        """
        return cls(id, mimetype, data, request_frames=request_frames)

    @classmethod
    def from_raw(cls, raw):
        """Creates an envelope from a tuple or list

        :param raw: Raw data for an envelope
        :type raw: tuple or list
        """
        request_frames = []
        raw_len = len(raw)
        request_frames_len = raw_len - MINIMUM_ENVELOPE_LEN - 1
        for i in range(request_frames_len):
            request_frames.append(raw[i])
        id, mimetype, data = raw[-MINIMUM_ENVELOPE_LEN:]
        return cls(id, mimetype, data, request_frames=request_frames)

    def __init__(self, id, mimetype, data, request_frames=None):
        self._id = id
        self._mimetype = mimetype
        self._data = data
        self._request_frames = request_frames or []

    @property
    def id(self):
        return self._id

    @property
    def mimetype(self):
        return self._mimetype

    @property
    def data(self):
        return self._data

    @property
    def request_frames(self):
        return self._request_frames

    def transfer_object(self):
        """This is the object to be sent over the wire. The reverse of this is
        Envelope.from_raw

        For zmq this should be an list
        """
        transfer_object = []
        if self._request_frames:
            transfer_object.extend(self._request_frames)
            transfer_object.append('')
        transfer_object.extend([self._id, self._mimetype, self._data])
        return transfer_object

    def response_envelope(self, mimetype, data, id=None):
        """Shortcut to create a response envelope from the current envelope

        By default this will create an envelope with the same request_frames,
        id and mimetype as this envelope.
        """
        id = id or self._id
        return Envelope.new(mimetype, data, id=id,
                request_frames=self._request_frames)
