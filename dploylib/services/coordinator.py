import threading
import logging
from dploylib.transport import Context
from .. import constants


logger = logging.getLogger('dploylib.services.coordinator')


class ServerCoordinatorFailing(Exception):
    pass


class ServerCoordinator(object):
    """A generic ServerCoordinator meant to be subclassed. It does not do any
    of the spawning of servers on it's own.

    :param control_uri: default ``inproc://control``, the uri for the service
        control socket
    :param context: default None, a :class:`~dploylib.transport.Context`
    """
    # This must be compatible with threading.Thread
    spawner = None
    logger = logger

    def __init__(self, control_uri='inproc://control', context=None):
        self._control_uri = control_uri
        self._context = context
        self._control_socket = None
        self._spawns = []

    @property
    def context(self):
        context = self._context
        if not context:
            context = self._context = Context.new()
        return context

    def setup_servers(self, server_config, settings):
        """Setup the servers"""
        spawn_settings = []
        for name, server in server_config:
            server_settings = settings.server_settings(name)
            spawn_settings.append((name, server, server_settings))
        self._spawn_settings = spawn_settings

    def start_control_socket(self):
        control_uri = self._control_uri
        self.logger.debug('Starting control socket @ "%s"' % control_uri)
        control_socket = self.context.socket('pub')
        control_socket.bind(control_uri)
        self._control_socket = control_socket

    def start(self):
        self.logger.debug('Starting coordinator')
        spawns = self._spawns
        self.start_control_socket()
        for name, server, server_settings in self._spawn_settings:
            context = self.server_context(name, server)
            spawn = self.spawn(server, name, server_settings, context=context)
            self.logger.debug('Server "%s" spawned' % name)
            spawns.append((name, spawn))

    def spawn(self, server, name, server_settings, **kwargs):
        """Spawn a server and return reference to the spawn"""
        spawn = self.spawner(target=self.start_server,
                args=(server, name, server_settings, self._control_uri),
                kwargs=kwargs)
        spawn.start()
        return spawn

    def server_context(self, name, server):
        """Creates and returns a context for the current server

        Defaults to returning the coordinator's context
        """
        return self.context

    def wait(self):
        """Poll the servers to see if they crash.

        If they do then stop everything
        """
        raise NotImplementedError('"wait" method must do something')

    def stop(self):
        """Stop the spawned servers"""
        raise NotImplementedError('"stop" method must do something')

    def start_server(self, server, name, server_settings, control_uri,
            **kwargs):
        new_server = server.new(name, server_settings, control_uri, **kwargs)
        new_server.start()


class ThreadedServerCoordinator(ServerCoordinator):
    spawner = threading.Thread

    def __init__(self, *args, **kwargs):
        self._thread_poll_duration = kwargs.pop('thread_poll_duration', 0.5)
        self._starting_thread_count = threading.active_count()
        super(ThreadedServerCoordinator, self).__init__(*args, **kwargs)

    def wait(self):
        # Threads are stored as the spawns of a server coordinator
        threads = self._spawns
        while True:
            some_dead = False
            for name, thread in threads:
                thread.join(self._thread_poll_duration)
                if not thread.is_alive():
                    self.logger.debug('Server "%s" has died' % name)
                    some_dead = True
            if some_dead:
                raise ServerCoordinatorFailing(
                        'Some servers have stopped working')

    def stop(self):
        control_socket = self._control_socket
        starting_thread_count = self._starting_thread_count
        while True:
            control_socket.send_text(constants.COORDINATOR_SHUTDOWN)
            for name, thread in self._spawns:
                thread.join(0.5)
            remaining = threading.active_count() - starting_thread_count
            if remaining <= 0:
                # All threads are done
                break
            else:
                logger.debug('Still waiting for %d thread(s)' % remaining)
