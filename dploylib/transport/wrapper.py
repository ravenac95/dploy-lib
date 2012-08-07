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


class Context(object):
    @classmethod
    def new(cls):
        context = zmq.Context()
        return cls(context)

    @classmethod
    def from_raw_context(cls, context):
        return cls(context)

    def __init__(self, context):
        self._context = context

    def socket(self, socket_type):
        return Socket.new(socket_type, context=self)


class Socket(object):
    @classmethod
    def new(cls, socket_type, context=None):
        context = context or Context.new()
        try:
            zmq_socket_type = _SOCKET_TYPE_MAP[socket_type.lower()]
        except KeyError:
            raise AttributeError('"%s" is an invalid socket_type name' %
                    socket_type)
        socket = context.socket(zmq_socket_type)
        return cls(socket, context)

    def __init__(self, socket, context):
        self._socket = socket
        self._context = context

    @property
    def zmq_context(self):
        return self._context

    @property
    def zmq_socket(self):
        return self._socket

    def set_option(self, option, value):
        socket_option = _SOCKET_OPTION_MAP[option]
        self._socket.setsockopt(socket_option, value)

    def bind(self, uri):
        self._socket.bind(uri)

    def connect(self, uri):
        self._socket.connect(uri)

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
        multipart_object = envelope.transport_object()
        self._socket.send_multipart(multipart_object)

    def receive_obj(self, handler):
        """Receives an envelope and calls an object to handle the envelope data

        The handler must be callable
        """
        envelope = self.receive_envelope()
        return handler(envelope)

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
        raw_envelope = self._socket.recv_multipart()
        return Envelope.from_raw(raw_envelope)
