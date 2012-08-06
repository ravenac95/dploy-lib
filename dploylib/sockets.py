"""
dploylib.sockets
~~~~~~~~~~~~~~~~

A wrapper around zmq sockets to handle. This allows us to control some things
globally on the transport layer. Eventually we will want to add encryption.
By having a standard data envelope we can do encryption as we need to.
"""
import zmq
import json


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
        return cls(id, data, mimetype)

    @classmethod
    def from_raw(cls, data):
        return cls(data[0], data[1], data[2])

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
        json_str = json.dumps(obj.__serialize__())
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

    def receive(self, handler):
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


class PollLoop(object):
    """A custom poller that automatically routes the handling of poll events

    The handlers of poll events are simply callables. This only handles POLLIN
    events at this time.
    """
    @classmethod
    def new(cls):
        poller = zmq.Poller()
        return cls(poller)

    def __init__(self, poller):
        self._poller = poller
        self._handler_map = {}

    def register(self, socket, handler):
        """Registers a socket or FD and it's handler to the poll loop"""
        # FIXME it let's anything through at the moment that isn't a dploy
        # socket
        raw_socket = socket
        if isinstance(socket, Socket):
            raw_socket = socket.zmq_socket
        self._handler_map[raw_socket] = [socket, handler]
        self._poller.register(raw_socket, zmq.POLLIN)

    def poll(self, timeout=None):
        sockets = dict(self._poller.poll(timeout=timeout))
        for raw_socket, handler_info in self._handler_map.iteritems():
            socket, handler = handler_info
            if raw_socket in sockets and sockets[raw_socket] == zmq.POLLIN:
                socket, handler = handler_info
                handler(socket)
