"""
dploylib.servers.observable
~~~~~~~~~~~~~~~~~~~~~~~~~~~

ObservableWorkService. This is a service that has two major components:

    1. A queue server to queue work requests
    2. A broadcast server to publish the process of the worker as it occurs

To use just subclass ObservableWorkerServer as follows::

    class MyService(ObservableWorkService):
        queue = QueueServer

And to start just do this::

    service = MyService.setup(queue_uri='uri', broadcast_in_uri='uri',
            broadcast_out_uri='uri', control_uri='uri')
    service.start()


The configuration will be passed directly to the queue and broadcast classes.


Possible usages::

    class MyService(ObservableWorkService):
        class SettingsMap:
            broadcast = {
                'in-uri': 'build-broadcast-in',
                'out-uri': 'build-broadcast-out',
            }
            queue = {
                'uri': 'queue-uri',
                'broadcast-in-uri': 'build-broadcast-in',
            }
        queue = BuildQueueServer
    service = MyService.setup(config)
    service.start()
"""


class ApplicationDying(Exception):
    pass


class ThreadedServerCoordinator(object):
    pass


class Service(object):
    """Controls a set of servers to provide a service over the network"""
    @classmethod
    def setup(cls, logger, settings, coordinator_cls=None):
        # Use threads by default
        coordinator_cls = coordinator_cls or ThreadedServerCoordinator
        service = cls(logger, settings, coordinator_cls)
        service.setup_service()
        return service

    def __init__(self, logger, settings, coordinator_cls):
        self._logger = logger
        self._settings = settings
        self._coordinator_cls = coordinator_cls

    def setup_service(self):
        settings = self._settings
        server_settings = self.setup_server_settings(settings)
        coordinator = self._coordinator_cls.setup(server_settings, settings)
        self._coordinator = coordinator

    def setup_server_settings(self):
        """Return objects of server settings"""
        raise NotImplementedError('"setup_server_settings" method must be '
                'implemented')

    def start(self):
        logger = self._logger
        coordinator = self._coordinator.start()
        try:
            coordinator.wait()
        except (KeyboardInterrupt, ApplicationDying):
            pass
        finally:
            logger.info('Shutting down. Waiting for child processes and '
                    'threads')
            coordinator.stop()
            logger.info('Shutdown complete.')


class PollLoop(object):
    pass


class ServerConfigError(Exception):
    pass


class EventServer(object):
    """A dploy server that utilizes a PollLoop to handle events"""
    @classmethod
    def create(cls, context, control_uri, settings):
        poll_loop = PollLoop.new()
        server = cls(context, control_uri, poll_loop, settings)
        server.setup_all()
        return server

    def __init__(self, context, control_uri, poll_loop, settings):
        self._context = context
        self._settings = settings
        self._poll_loop = poll_loop
        self._control_uri = control_uri

    def setup_all(self):
        self._connect_to_server_control_socket()

        input_sockets = self.setup_sockets()

        for socket_name, socket in input_sockets.iteritems():
            socket_handler = getattr(self, 'handle_%' % socket_name, None)
            if not socket_handler:
                raise ServerConfigError('No handler defined for socket "%s"' %
                        socket_name)
            self._poll_loop.register(socket, socket_handler)

    def _connect_to_server_control_socket(self):
        server_control_socket = self._context.socket('sub')
        server_control_socket.setsockopt('subscribe', '__control__')
        server_control_socket.connect(self._control_uri)
        self._server_control_socket = server_control_socket
        self._poll_loop.register(server_control_socket,
                self.handle_server_control)

    def handle_server_control(self, socket):
        control_text = socket.receive_text()
        if control_text == 'shutdown':
            # Log this
            # Raise an error to stop the server
            raise Exception

    def setup_sockets(self):
        """Setup the necessary sockets.

        Should return a dictionary of input sockets
        """
        return {}

    def run(self):
        try:
            self._poll_loop.poll()
        except:
            # FIXME Log here
            break


class Socket(object):
    pass


class BroadcastServer(EventServer):
    """Broadcasts messages it received from a PULL socket to any listeners"""
    def setup_sockets(self):
        in_socket = Socket.new('pull', context=self._context)
        in_socket.bind(self._settings['in-uri'])
