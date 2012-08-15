import json
import logging
from dploylib import constants
from dploylib.transport import Context, PollLoop

logger = logging.getLogger('dploylib.servers.server')


def bind_in(name, socket_type, obj=None):
    """A decorator that creates a SocketDescription describing a socket bound
    to receive input. The decorated function or method is used as the input
    event handler.

    :param name: The name of the socket (for configuration purposes)
    :param socket_type: The lowercase name of the zeromq socket type
    :type socket_type: str
    :param obj: (optional) A class or object that implements the
        ``deserialize`` method to deserialize incoming data
    :returns: A :class:`SocketDescription`
    """
    setup_type = 'bind'

    def decorator(f):
        return SocketDescription(name, socket_type, setup_type,
                input_handler=f, deserializer=obj)
    return decorator


def connect_in(name, socket_type, obj=None):
    """A decorator that creates a SocketDescription describing a socket
    connected to receive input. The decorated function or method is used as the
    input event handler.

    :param name: The name of the socket (for configuration purposes)
    :param socket_type: The lowercase name of the zeromq socket type
    :type socket_type: str
    :param obj: (optional) A class or object that implements the
        ``deserialize`` method to deserialize incoming data
    :returns: A :class:`SocketDescription`
    """
    setup_type = 'connect'

    def decorator(f):
        return SocketDescription(name, socket_type, setup_type,
                input_handler=f, deserializer=obj)
    return decorator


def bind(name, socket_type):
    """A decorator that creates a SocketDescription that describes a bound
    socket. This socket does not listen for input.

    :param name: The name of the socket (for configuration purposes)
    :param socket_type: The lowercase name of the zeromq socket type
    :type socket_type: str
    """
    setup_type = 'bind'
    return SocketDescription(name, socket_type, setup_type)


def connect(name, socket_type):
    """A decorator that creates a SocketDescription that describes a connected
    socket. This socket does not listen for input.

    :param name: The name of the socket (for configuration purposes)
    :param socket_type: The lowercase name of the zeromq socket type
    :type socket_type: str
    """
    setup_type = 'connect'
    return SocketDescription(name, socket_type, setup_type)


class DataNotDeserializable(Exception):
    pass


class SocketReceived(object):
    """Stores data received on a socket. This is essentially a request object
    for dploy Servers. The name is SocketReceived because the servers aren't
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


class SocketHandlerWrapper(object):
    """Wraps the handling function for a socket"""
    def __init__(self, server, handler, deserializer=None):
        self._server = server
        self._handler = handler
        self._deserializer = deserializer

    def __call__(self, socket):
        envelope = socket.receive_envelope()
        received = SocketReceived(envelope, self._deserializer)
        self._handler(self._server, socket, received)


class SocketDescription(object):
    """Describes a socket. This is the low level class used by :func:`bind_in`,
    :func:`bind`, :func:`connect_in`, and :func:`connect`

    :param name: The name of the socket. This is used when searching the
        settings for a socket's settings
    :param socket_type: The type of socket. One of 'rep', 'req', 'pub', 'sub',
        'push', 'pull', 'pair', 'router', or 'dealer'.
    :param setup_type: The setup type. Either 'bind' or 'connect'
    :param input_handler: The handling function/method for this socket
    :param deserializer: (optional) A class that implements a
        method/classmethod ``deserialize`` which is used to deserialize any
        data in the envelope
    :param default_options: (optional) Default list of 2-tuple options to apply
        to the socket
    """
    def __init__(self, name, socket_type, setup_type, input_handler=None,
            deserializer=None, default_options=None):
        self._socket_type = socket_type
        self._setup_type = setup_type
        self._input_handler = input_handler
        self._deserializer = deserializer
        self._name = name

    def create_socket(self, context, uri, options):
        socket = context.socket(self._socket_type)
        setup_method = getattr(socket, self._setup_type)
        setup_method(uri)
        for option_name, option_value in options:
            socket.set_option(option_name, option_value)
        return socket

    @property
    def name(self):
        return self._name

    def handler(self, server):
        """A SocketHandlerWrapper"""
        input_handler = self._input_handler
        if not input_handler:
            return None
        return SocketHandlerWrapper(server, self._input_handler,
                self._deserializer)


class ServerDescription(object):
    """Provides the socket description of a :class:`DployServer`"""
    @classmethod
    def new(cls, name, settings, control_uri, context=None):
        server_description = cls()
        server = server_description.create_server(name, settings, control_uri,
                context)
        return server

    def create_server(self, server_name, settings, control_uri, context):
        """Creates the actual server instance using :class:`DployServer`

        :param server_name: The name of the server
        :param settings: A settings object for a particular server
        :param control_uri: A URI to the socket that controls this server
        :param context: The :class:`~dploylib.transport.Context` for this
            server
        """
        real_server = DployServer.new(server_name, settings, control_uri,
                context)
        descriptions_iter = self.iter_socket_descriptions()
        for local_name, description in descriptions_iter:
            real_server.add_socket_from_description(description)
        return real_server

    def iter_socket_descriptions(self):
        """Iterate through all the socket descriptions on this
        ServerDescription

        :returns: An iterator of ([name], [socket_description])
        """
        class_iteritems = self.__class__.__dict__.iteritems()
        socket_descriptions = []
        for name, value in class_iteritems:
            if hasattr(value, 'create_socket'):
                socket_descriptions.append((name, value))
        return socket_descriptions


# Use Server description as a facade
Server = ServerDescription


class DployServer(object):
    """The actual server behind the scenes"""
    logger = logger

    @classmethod
    def new(cls, name, settings, control_uri, context=None):
        context = context or Context.new()
        server = cls(name, settings, control_uri, context)
        server.connect_to_control()
        return server

    def __init__(self, name, settings, control_uri, context,
            poll_loop=None):
        self._context = context
        self._name = name
        self._settings = settings
        self._control_uri = control_uri
        self._control_socket = None
        self._poll_loop = poll_loop or PollLoop.new()
        self.sockets = SocketStorage()

    def connect_to_control(self):
        control_uri = self._control_uri
        control_socket = self._context.socket('sub')
        control_socket.set_option('subscribe', '')
        control_socket.connect(control_uri)
        self._control_socket = control_socket
        self.add_socket('_server_control', control_socket,
                handler=self._handle_server_control)

    def _handle_server_control(self, socket):
        text = socket.receive_text()
        if text == constants.COORDINATOR_SHUTDOWN:
            raise ServerStopped()

    def start(self):
        """Run the poll loop for the server"""
        self.logger.debug('Starting server "%s"' % self._name)
        while True:
            try:
                self._poll_loop.poll()
            except ServerStopped:
                self.logger.debug('Stopping server "%s"' % self._name)
                break

    def add_socket(self, name, socket, handler=None):
        """Add the socket and it's handler"""
        self.sockets.register(name, socket)
        self._poll_loop.register(socket, handler)

    def add_socket_from_description(self, description):
        name = description.name
        socket_info = self._settings.socket_info(name)
        uri = socket_info['uri']
        options = socket_info.get('options', [])
        socket = description.create_socket(self._context, uri, options)
        handler = description.handler(self)
        self.add_socket(name, socket, handler)


class ServerStopped(Exception):
    pass


class SocketStorage(object):
    """The storage of the sockets"""
    def __init__(self):
        self._storage = {}

    def register(self, name, socket):
        self._storage[name] = socket

    def __getattr__(self, name):
        return self._storage[name]
