from nose.tools import eq_
from testkit import *
from mock import Mock, patch
from dploylib.clients.base import *


class TestRequestClient(object):
    def setup(self):
        class RequestClientForTesting(BaseRequestClient):
            obj = 'fakeobj'

        self.mock_context = Mock()

        self.client = RequestClientForTesting('fakeuri', self.mock_context)

    def test_connect(self):
        self.client.connect()

        self.mock_context.socket.assert_called_with('req')
        mock_socket = self.mock_context.socket.return_value

        mock_socket.connect.assert_called_with('fakeuri')

    @patch('dploylib.clients.base.ReceivedData')
    def test_request(self, mock_received):
        mock_socket = self.client._request_socket = Mock()
        some_obj = 'someobj'

        response = self.client.request(some_obj)

        mock_socket.send_obj.assert_called_with(some_obj)

        mock_envelope = mock_socket.receive_envelope.return_value
        mock_received.assert_called_with(mock_envelope, 'fakeobj')

        eq_(response, mock_received.return_value)


class TestListeningClient(object):
    def setup(self):
        class ListeningClientForTesting(BaseListeningClient):
            obj = 'fakeobj'

        self.mock_context = Mock()
        self.client = ListeningClientForTesting('fakeuri', 'fakeid',
                self.mock_context)

    def test_connect(self):
        self.client.connect()

        self.mock_context.socket.assert_called_with('sub')
        mock_socket = self.mock_context.socket.return_value

        mock_socket.connect.assert_called_with('fakeuri')
        mock_socket.set_option.assert_called_with('subscribe', 'fakeid')

    @patch('dploylib.clients.base.ReceivedData')
    def test_listen(self, mock_received):
        mock_socket = self.client._listening_socket = Mock()

        def fake_handler(socket, received, stop):
            assert socket == mock_socket
            assert received == mock_received.return_value
            stop()
        self.client.listen(fake_handler)

        mock_socket.receive_envelope.assert_called_with()
        mock_envelope = mock_socket.receive_envelope.return_value
        mock_received.assert_called_with(mock_envelope, 'fakeobj')
