import json
from dploylib.transport import Context, PollLoop


def bind_in(name, socket_type, obj=None):
    setup_type = "bind"

    def decorator(f):
        return SocketDescription(name, socket_type, setup_type,
                input_handler=f, deserializer=obj)
    return decorator


def connect_in(name, socket_type, obj=None):
    setup_type = "connect"

    def decorator(f):
        return SocketDescription(name, socket_type, setup_type,
                input_handler=f, deserializer=obj)
    return decorator


def bind(name, socket_type):
    setup_type = "bind"
    return SocketDescription(name, socket_type, setup_type)


def connect(name, socket_type):
    setup_type = 'connect'
    return SocketDescription(name, socket_type, setup_type)


class DataNotDeserializable(Exception):
    pass


class SocketReceived(object):
    """Stores data received on a socket"""
    def __init__(self, envelope, deserializer):
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
    def __init__(self, server, handler, deserializer=None):
        self._server = server
        self._handler = handler
        self._deserializer = deserializer

    def __call__(self, socket):
        envelope = socket.receive_envelope()
        received = SocketReceived(envelope, self._deserializer)
        self._handler(self._server, received)


class SocketDescription(object):
    def __init__(self, name, socket_type, setup_type, input_handler=None,
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
        return SocketHandlerWrapper(server, self._input_handler,
                self._deserializer)


class ServerDescription(object):
    """Dploy Server. This is a description of a real server

    """
    @classmethod
    def new(cls, name, settings, control_uri, context=None):
        server_description = cls()
        server = server_description.create_server(name, settings, control_uri,
                context)
        return server

    def create_server(self, server_name, settings, control_uri, context):
        """Creates the actual server using the DployServer class"""
        real_server = DployServer.new(server_name, settings, control_uri,
                context)
        descriptions_iter = self.iter_socket_descriptions()
        for local_name, description in descriptions_iter:
            real_server.add_socket_from_description(description)
        return real_server

    def iter_socket_descriptions(self):
        """Gather all the socket descriptions for this server"""
        class_iteritems = self.__class__.__dict__.iteritems()
        socket_descriptions = []
        for name, value in class_iteritems:
            print SocketDescription.__class__
            if hasattr(value, 'create_socket'):
                socket_descriptions.append((name, value))
        return socket_descriptions


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
