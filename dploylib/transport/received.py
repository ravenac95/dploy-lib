# -*- coding: utf-8 -*-

"""
dploylib.transport.received
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines a wrapper for received data on a socket. This can be used in
conjunction with socket.receive_envelope.
"""

import json


class DataNotDeserializable(Exception):
    pass


class ReceivedData(object):
    """Stores data received on a socket. This is essentially a request object
    for dploy Servers. The name is ReceivedData because the servers aren't
    necessarily reacting to requests.

    :param envelope: The received
        :class:`~dploylib.transport.envelope.Envelope`
    :param deserializer: (optional) A class that implements a classmethod
        ``deserialize`` which is used to deserialize any data in the envelope
    """
    def __init__(self, envelope, deserializer=None):
        self.envelope = envelope
        self._deserializer = deserializer
        self._json = None
        self._obj = None

    @property
    def json(self):
        """If the mimetype for the data is application/json return json"""
        json_data = self._json
        if not json_data:
            envelope = self.envelope
            if envelope.mimetype == 'application/json':
                json_data = json.loads(envelope.data)
                self._json = json_data
        return json_data

    @property
    def obj(self):
        """Grab the object represented by the json data"""
        deserializer = self._deserializer
        if not deserializer:
            return None
        obj = self._obj
        if not obj:
            json_data = self.json
            if json_data is None:
                raise DataNotDeserializable()
            obj = deserializer.deserialize(json_data)
            self._obj = obj
        return obj
