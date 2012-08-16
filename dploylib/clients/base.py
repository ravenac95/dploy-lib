"""
dploylib.clients.base
~~~~~~~~~~~~~~~~~~~~~

The base client for dploy services.
"""
from dploylib.transport import *


class StopListening(Exception):
    pass


class BaseRequestClient(object):
    socket_type = 'req'
    obj = None

    def __init__(self, request_uri, context):
        self._request_uri = request_uri
        self._context = context
        self._request_socket = None

    def connect(self):
        context = self._context
        # Setup request socket
        request_socket = context.socket(self.socket_type)
        request_socket.connect(self._request_uri)
        self._request_socket = request_socket

    def request(self, request_obj, **options):
        request_socket = self._request_socket
        request_socket.send_obj(request_obj, **options)
        envelope = request_socket.receive_envelope()
        return ReceivedData(envelope, self.obj)


def stop_listening():
    raise StopListening('Listening Stopped')


class BaseListeningClient(object):
    socket_type = 'sub'
    obj = None

    def __init__(self, listening_uri, listening_id, context):
        self._listening_uri = listening_uri
        self._listening_id = listening_id
        self._context = context
        self._listening_socket = None

    def connect(self):
        context = self._context
        # Setup request socket
        listening_socket = context.socket(self.socket_type)
        listening_socket.set_option('subscribe', self._listening_id)
        listening_socket.connect(self._listening_uri)
        self._listening_socket = listening_socket

    def listen(self, handler):
        while True:
            envelope = self._listening_socket.receive_envelope()
            received = ReceivedData(envelope, self.obj)
            try:
                handler(self._listening_socket, received, stop_listening)
            except StopListening:
                break
            except:
                raise
