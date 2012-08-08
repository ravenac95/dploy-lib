from mock import Mock
import zmq
from dploylib.transport import Socket
from dploylib.transport.poll import *


def test_initialize_poll_loop():
    PollLoop.new()

class TestPollLoop(object):
    def setup(self):
        self.mock_zmq_poller = Mock()
        self.poll_loop = PollLoop(self.mock_zmq_poller)

    def test_register_dploylib_socket(self):
        mock_socket = Mock(spec=Socket)
        mock_handler = Mock()
        mock_zmq_socket = mock_socket.zmq_socket

        self.poll_loop.register(mock_socket, mock_handler)

        self.mock_zmq_poller.register.assert_called_with(
                mock_zmq_socket, zmq.POLLIN)

    def test_register_other(self):
        mock_socket = Mock()
        mock_handler = Mock()

        self.poll_loop.register(mock_socket, mock_handler)

        self.mock_zmq_poller.register.assert_called_with(
                mock_socket, zmq.POLLIN)

    def test_poll(self):
        timeout = 30
        self.mock_zmq_poller.poll.return_value = []
        self.poll_loop.poll(timeout=timeout)
        self.mock_zmq_poller.poll.assert_called_with(timeout=timeout)


class TestPollLoopWithRegistrations(object):
    """Test PollLoop with registered handlers"""
    def setup(self):
        self.mock_zmq_poller = Mock()

        self.mock_socket1 = Mock(spec=Socket)
        self.mock_raw_socket1 = self.mock_socket1.zmq_socket
        self.mock_handler1 = Mock()

        self.mock_socket2 = Mock()
        self.mock_raw_socket2 = self.mock_socket2
        self.mock_handler2 = Mock()

        self.poll_loop = PollLoop(self.mock_zmq_poller)

        self.poll_loop.register(self.mock_socket1, self.mock_handler1)
        self.poll_loop.register(self.mock_socket2, self.mock_handler2)

    def set_poll_return(self, socket_numbers):
        return_value = {}
        for num in socket_numbers:
            raw_socket = getattr(self, 'mock_raw_socket%d' % num)
            return_value[raw_socket] = zmq.POLLIN
        self.mock_zmq_poller.poll.return_value = return_value

    def test_poll1(self):
        self.set_poll_return([1])

        self.poll_loop.poll()

        self.mock_handler1.assert_called_with(self.mock_socket1)

    def test_poll2(self):
        self.set_poll_return([2])

        self.poll_loop.poll()

        self.mock_handler2.assert_called_with(self.mock_socket2)

    def test_poll_both(self):
        self.set_poll_return([1,2])

        self.poll_loop.poll()

        self.mock_handler1.assert_called_with(self.mock_socket1)
        self.mock_handler2.assert_called_with(self.mock_socket2)
