# -*- coding: utf-8 -*-

"""
dploylib.transport.poll
~~~~~~~~~~~~~~~~~~~~~~~

This module defines the PollLoop
"""

import logging
import zmq
from .wrapper import Socket

logger = logging.getLogger('dploylib.transport.poll')


class PollLoop(object):
    """A custom poller that automatically routes the handling of poll events

    The handlers of poll events are simply callables. This only handles POLLIN
    events at this time.
    """
    logger = logger

    @classmethod
    def new(cls):
        poller = zmq.Poller()
        return cls(poller)

    def __init__(self, poller):
        self._poller = poller
        self._handler_map = {}

    def register(self, socket, handler):
        """Registers a socket or FD and it's handler to the poll loop"""
        # FIXME? it let's anything through at the moment that isn't a dploy
        # socket it even has a test that asserts this at this time, maybe we
        # can do something better later
        self.logger.debug('Registering handler: %r for socket: %r' %
                (handler, socket))
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
