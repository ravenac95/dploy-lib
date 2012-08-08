import zmq
import json
from .envelope import Envelope

TEXT_MIMETYPE = 'text/plain'

_SOCKET_TYPE_MAP = {
    'pull': zmq.PULL,
    'push': zmq.PUSH,
    'pub': zmq.PUB,
    'sub': zmq.SUB,
    'req': zmq.REQ,
    'rep': zmq.REP,
    'router': zmq.ROUTER,
    'dealer': zmq.DEALER,
    'pair': zmq.PAIR,
}

_SOCKET_OPTION_MAP = {
    'hwm': zmq.HWM,
    'swap': zmq.SWAP,
    'affinity': zmq.AFFINITY,
    'identity': zmq.IDENTITY,
    'subscribe': zmq.SUBSCRIBE,
    'unsubscribe': zmq.UNSUBSCRIBE,
}


def clean_option_value(value):
    if isinstance(value, (str, int)):
        return value
    elif isinstance(value, (unicode)):
        return value.encode('utf-8')
    raise ValueError('Option must be str, int, or unicode')


def get_zmq_constant(name):
    return getattr(zmq, name.upper())


class Context(object):
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
    @classmethod
    def new(cls, socket_type, context=None):
        context = context or Context.new()
        socket = context.socket(socket_type)
        return socket

    @classmethod
    def connect_new(cls, socket_type, uri, options=None, context=None):
        """Create and connect a new socket"""
        socket = cls.new(socket_type, context=context)
        options = options or []
        for option, value in options:
            socket.set_option(option, value)
        socket.connect(uri)
        return socket

    @classmethod
    def bind_new(cls, socket_type, uri, options=None, context=None):
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
        socket_option = get_zmq_constant(option)
        cleaned_option = clean_option_value(value)
        self.zmq_socket.setsockopt(socket_option, cleaned_option)

    def bind(self, uri):
        self.zmq_socket.bind(uri)

    def bind_to_random(self, uri, min_port=None, max_port=None,
            max_tries=None):
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
        self.zmq_socket.connect(uri)

    def send_obj(self, obj, id=''):
        """Sends encoded an object as encoded data.

        The encoding can be anything. Default is JSON. This could change later
        and should not affect communications.

        The object must implement the method __serialize__
        """
        mimetype = 'application/json'
        json_str = json.dumps(obj.serialize())
        envelope = Envelope.new(mimetype, json_str, id=id)
        self.send_envelope(envelope)

    def send_text(self, text, id=''):
        """Sends a simple text message"""
        mimetype = 'text/plain'
        envelope = Envelope.new(mimetype, text, id=id)
        self.send_envelope(envelope)

    def send_envelope(self, envelope):
        """Send an envelope"""
        multipart_object = envelope.transfer_object()
        self.zmq_socket.send_multipart(multipart_object)

    def receive_obj(self, handler):
        """Receives an envelope and calls an object to handle the envelope data

        The handler must be callable
        """
        envelope = self.receive_envelope()
        obj_data = json.loads(envelope.data)
        return handler(obj_data)

    def receive_text(self):
        """Convenience handler to receive plain text"""
        envelope = self.receive_envelope()
        mimetype = envelope.mimetype
        if mimetype != TEXT_MIMETYPE:
            raise ValueError('Expected envelope with mimetype "%s" instead '
                    'received "%s"' % (TEXT_MIMETYPE, mimetype))
        return envelope.data

    def receive_envelope(self):
        """Receive an envelope"""
        raw_envelope = self.zmq_socket.recv_multipart()
        return Envelope.from_raw(raw_envelope)
