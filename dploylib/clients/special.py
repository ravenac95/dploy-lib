from .base import *


class BroadcastMessage(object):
    pass


class ObservableServiceClient(object):
    """A client that sends requests and listens for data"""
    def __init__(self, request_uri, observe_uri, observe_id, context):
        self._request_uri = request_uri
        self._observe_uri = observe_uri
        self._observe_id = observe_id
        self._context = context
        self._request_client = None
        self._listening_client = None

    def connect(self):
        # Setup observe socket
        pass

    def request(self, request_obj):
        self.connect()
        request_socket = self._request_socket
        observe_socket = self._observe_socket

        request_socket.send_obj(request_obj)
