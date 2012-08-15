# -*- coding: utf-8 -*-

"""
dploylib.transport.wrappers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module defines a thin wrapper around zmq. This will allow dploy's stack to
change certain behaviour by simply changing this library.
"""

import json
import zmq
from .envelope import Envelope

TEXT_MIMETYPE = 'text/plain'


def clean_option_value(value):
    if isinstance(value, (str, int)):
        return value
    elif isinstance(value, (unicode)):
        return value.encode('utf-8')
    raise ValueError('Option must be str, int, or unicode')


def get_zmq_constant(name):
    return getattr(zmq, name.upper())


class Context(object):
    """A wrapper around a zeromq Context"""
    @classmethod
    def new(cls):
        context = zmq.Context()
        return cls(context)

    @classmethod
    def from_raw_context(cls, context):
        return cls(context)

    def __init__(self, zmq_context):
        self._zmq_context = zmq_context

    def socket(self, socket_type):
        zmq_socket_type = get_zmq_constant(socket_type)
        zmq_socket = self._zmq_context.socket(zmq_socket_type)
        return Socket(zmq_socket, self)


class Socket(object):
    """A wrapper around a zeromq Socket"""
    @classmethod
    def new(cls, socket_type, context=None):
        """Creates a new socket

        :param socket_type: Name of the socket type
        :type socket_type: str
        :param context: (optional) A :class:`Context`. Defaults to creating a
            new :class:`Context`
        """
        context = context or Context.new()
        socket = context.socket(socket_type)
        return socket

    @classmethod
    def connect_new(cls, socket_type, uri, options=None, context=None):
        """Create and connect a new socket

        :param socket_type: Name of the socket type
        :type socket_type: str
        :param uri: URI of the socket to connect to
        :param context: (optional) A :class:`Context`. Defaults to creating a
            new :class:`Context`
        """
        socket = cls.new(socket_type, context=context)
        options = options or []
        for option, value in options:
            socket.set_option(option, value)
        socket.connect(uri)
        return socket

    @classmethod
    def bind_new(cls, socket_type, uri, options=None, context=None):
        """Create and bind a new socket

        :param socket_type: Name of the socket type
        :type socket_type: str
        :param uri: URI of the socket to bind to
        :param context: (optional) A :class:`Context`. Defaults to creating a
            new :class:`Context`
        """
        socket = cls.new(socket_type, context=context)
        options = options or []
        for option, value in options:
            socket.setup_option(option, value)
        socket.bind(uri)
        return socket

    def __init__(self, zmq_socket, zmq_context):
        self._zmq_socket = zmq_socket
        self._zmq_context = zmq_context

    @property
    def zmq_context(self):
        return self._zmq_context

    @property
    def zmq_socket(self):
        return self._zmq_socket

    def set_option(self, option, value):
        """Set a socket option

        :param option: Name of the option
        :type option: str
        :param value: Value of the option
        :type value: str or int. Depends on the option.
        """
        socket_option = get_zmq_constant(option)
        cleaned_option = clean_option_value(value)
        self.zmq_socket.setsockopt(socket_option, cleaned_option)

    def bind(self, uri):
        """Bind the socket to a URI"""
        self.zmq_socket.bind(uri)

    def bind_to_random(self, uri, min_port=None, max_port=None,
            max_tries=None):
        """Bind the socket to a random port at URI"""
        kwargs = {}
        if min_port:
            kwargs['min_port'] = min_port
        if max_port:
            kwargs['max_port'] = max_port
        if max_tries:
            kwargs['max_tries'] = max_tries
        port = self.zmq_socket.bind_to_random_port(uri, **kwargs)
        return port

    def connect(self, uri):
        """Connect the socket to a URI"""
        self.zmq_socket.connect(uri)

    def send_obj(self, obj, id=''):
        """Sends encoded an object as encoded data.

        The encoding can be anything. Default is JSON. This could change later
        and should not affect communications.

        The object must implement the method __serialize__

        :param obj: An object that implements a serialize method that returns
            any data that can be serialized (ie. lists, dict, strings, ints)
        :param id: The id for the envelope. Defaults to ''
        """

        mimetype = 'application/json'
        json_str = json.dumps(obj.serialize())
        envelope = Envelope.new(mimetype, json_str, id=id)
        self.send_envelope(envelope)

    def send_text(self, text, id=''):
        """Sends a simple text message

        :param text: Text to send
        :param id: The id for the envelope. Defaults to ''
        """
        mimetype = 'text/plain'
        envelope = Envelope.new(mimetype, text, id=id)
        self.send_envelope(envelope)

    def send_envelope(self, envelope):
        """Send an :class:`~dploylib.transport.envelope.Envelope`"""
        multipart_object = envelope.transfer_object()
        self.zmq_socket.send_multipart(multipart_object)

    def receive_obj(self, handler):
        """Receives an :class:`~dploylib.transport.envelope.Envelope` and calls
        an object to handle the envelope data.

        :param handler: A callable that transforms the data into an object
        """
        envelope = self.receive_envelope()
        obj_data = json.loads(envelope.data)
        return handler(obj_data)

    def receive_text(self):
        """Convenience method to receive plain text"""
        envelope = self.receive_envelope()
        mimetype = envelope.mimetype
        if mimetype != TEXT_MIMETYPE:
            raise ValueError('Expected envelope with mimetype "%s" instead '
                    'received "%s"' % (TEXT_MIMETYPE, mimetype))
        return envelope.data

    def receive_envelope(self):
        """Receive an :class:`~dploylib.transport.envelope.Envelope`"""
        raw_envelope = self.zmq_socket.recv_multipart()
        return Envelope.from_raw(raw_envelope)
