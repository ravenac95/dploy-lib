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


    """
    @classmethod
    def new(cls, mimetype, data, id=''):
        return cls(id, mimetype, data)

    @classmethod
    def from_raw(cls, raw):
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
        """This is the object to be send over the wire.

        For zmq this should be an array
        """
        return [self._id, self._mimetype, self._data]
