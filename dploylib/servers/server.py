import json
from dploylib.transport import Context, PollLoop


__all__ = ['Server', 'bind_in', 'bind', 'connect_in', 'connect']


class SocketDescriptor(object):
    def __init__(self, socket_type, setup_type, input_handler=None,
            name=None, deserializer=None):
        self._socket_type = socket_type
        self._setup_type = setup_type
        self._input_handler = input_handler
        self._name = name
        self._deserializer = deserializer

    def __get__(self, instance, instance_type=None):
        socket_description = SocketDescription(self._socket_type,
                self._setup_type, self._input_handler, name=self._name,
                deserializer=self._deserializer)
        return socket_description


def bind_in(name, socket_type, obj=None):
    setup_type = "bind"

    def decorator(f):
        socket_name = name or f.__name__
        return SocketDescriptor(socket_type, setup_type, input_handler=f,
                name=socket_name, deserializer=obj)
    return decorator


def connect_in(name, socket_type, obj=None):
    setup_type = "connect"

    def decorator(f):
        socket_name = name or f.__name__
        return SocketDescriptor(socket_type, setup_type, input_handler=f,
                name=socket_name)
    return decorator


def bind(name, socket_type):
    setup_type = "bind"
    return SocketDescriptor(socket_type, setup_type, name=name)


def connect(name, socket_type):
    setup_type = 'connect'
    return SocketDescriptor(socket_type, setup_type, name=name)


class SocketReceived(object):
    """Stores data received on a socket"""
    def __init__(self, envelope, data, obj=None):
        self.envelope = envelope
        self.obj = obj

    @property
    def json(self):
        """If the mimetype for the data is application/json return json"""
        envelope = self.envelope
        if envelope.mimetype == 'application/json':
            return json.loads(envelope.data)


class SocketHandlerWrapper(object):
    def __init__(self, handler, deserializer=None):
        self._handler = handler
        self._deserializer = deserializer

    def __call__(self, socket):
        envelope = socket.receive_envelope()
        if envelope.data


class SocketDescription(object):
    def __init__(self, socket_type, setup_type, input_handler, name=None,
            deserializer=None, default_options=None):
        """Create a socket description

        :param socket_type: the type of socket
        :type socket_type: str
        :param setup_type: 'connect' or 'bind'
        :type setup_type: str
        :param input_handler: (optional) a function to handle input
        :type input_handler: str
        :param name: (optional) name of the socket
        :type name: str
        """
        self._socket_type = socket_type
        self._setup_type = socket_type
        self._input_handler = input_handler
        self._deserializer = deserializer
        self._name = name

    def create_socket(self, context, uri, options):
        socket = context.socket(self._socket_type, self._setup_type)
        for option_name, option_value in options:
            socket.set_option(option_name, option_value)
        return socket

    @property
    def name(self):
        return self._name

    @property
    def handler(self):
        """A SocketHandlerWrapper"""
        pass


class ServerDescription(object):
    """Dploy Server. This is a description of a real server

    """
    @classmethod
    def new(cls, name, settings, control_uri, context=None):
        server_description = cls()
        server = server_description.create_server(name, settings, control_uri,
                context)
        return server

    def __init__(self):
        pass

    def create_server(self, server_name, settings, control_uri, context):
        """Creates the actual server using the DployServer class"""
        real_server = DployServer.new(server_name, settings, control_uri,
                context)
        descriptions_iter = self.iter_socket_descriptions()
        for local_name, description in descriptions_iter:
            real_server.add_socket_from_description(description)
        return real_server

    def gather_socket_descriptions(self):
        """Gather all the socket descriptions for this server"""
        pass

# Use Server description as a facade
Server = ServerDescription


class DployServer(object):
    """The actual server behind the scenes"""
    @classmethod
    def new(cls, name, settings, control_uri, context=None):
        context = context or Context.new()
        server = cls(name, settings, control_uri, context)
        server.connect_to_control()
        return server

    def __init__(self, name, settings, control_uri, context):
        self._context = context
        self._name = name
        self._settings = settings
        self._control_uri = control_uri
        self._control_socket = None
        self._poll_loop = PollLoop.new()
        self.sockets = None

    def connect_to_control(self):
        control_uri = self._control_uri
        control_socket = self._context.socket('sub')
        control_socket.set_option('subscribe', '')
        control_socket.connect(control_uri)
        self._control_socket = control_socket
        self.add_socket('_server_control', control_socket,
                handler=self._handler_server_control)

    def _handle_server_control(self, received):
        pass

    def start(self):
        """Run the poll loop for the server"""
        pass

    def add_socket(self, name, socket, handler=None):
        """Add the socket and it's handler"""
        pass

    def add_socket_from_description(self, description):
        name = description.name
        socket_info = self._settings.socket_info(name)
        uri = socket_info['uri']
        options = socket_info.get('options', [])
        socket = description.create_socket(self._context, uri, options)
        self.add_socket(name, socket, description.handler)
