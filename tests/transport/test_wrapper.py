import zmq
from mock import patch, Mock
from nose.tools import eq_, raises
from dploylib.transport.wrapper import *


@patch('zmq.Context')
def test_context_created_correctly(mock_zmq_context_cls):
    context = Context.new()

    mock_zmq_context_cls.assert_called_with()

    eq_(isinstance(context, Context), True)


@patch('dploylib.transport.wrapper.Socket')
def test_context_creates_socket(mock_socket_cls):
    mock_zmq_context = Mock()
    context = Context(mock_zmq_context)
    context.socket('pub')
    mock_zmq_context.socket.assert_called_with(zmq.PUB)


@patch('dploylib.transport.wrapper.Context')
def test_socket_created_correctly(mock_context_cls):
    socket = Socket.new('pub')

    mock_context = mock_context_cls.new.return_value
    mock_context.socket.assert_called_wth('pub')

    eq_(socket, mock_context.socket.return_value)


class TestSocket(object):
    def setup(self):
        self.mock_zmq_socket = Mock()
        self.mock_zmq_context = Mock()

        self.socket = Socket(self.mock_zmq_socket,
                zmq_context=self.mock_zmq_context)

    @patch('dploylib.transport.wrapper.get_zmq_constant')
    def test_socket_set_option_better(self, mock_get_zmq_constant):
        # Setup
        mock_expected_option = mock_get_zmq_constant.return_value
        option = 'option'
        value = 'value'

        # Test
        self.socket.set_option(option, value)

        # Assertions
        mock_get_zmq_constant.assert_called_with(option)
        self.mock_zmq_socket.setsockopt.assert_called_with(
                mock_expected_option, value)

    def test_socket_set_option(self):
        tests = [
            ['hwm', 0, zmq.HWM],
            ['swap', 1, zmq.SWAP],
            ['affinity', 2, zmq.AFFINITY],
            ['identity', 3, zmq.IDENTITY],
            ['subscribe', u'a', zmq.SUBSCRIBE],
            ['unsubscribe', u'b', zmq.UNSUBSCRIBE],
        ]
        for option, value, expected_opt in tests:
            yield self.do_set_option, option, value, expected_opt

    def do_set_option(self, option, value, expected_opt):
        self.socket.set_option(option, value)

        self.mock_zmq_socket.setsockopt.assert_called_with(expected_opt,
                value)

    def test_bind(self):
        uri = 'uri'

        self.socket.bind(uri)

        self.mock_zmq_socket.bind.assert_called_with(uri)

    def test_connect(self):
        uri = 'uri'

        self.socket.connect(uri)

        self.mock_zmq_socket.connect.assert_called_with(uri)

    @patch('json.dumps')
    @patch('dploylib.transport.wrapper.Envelope')
    def test_send_obj(self, mock_envelope_cls, mock_dumps):
        mock_obj = Mock()
        mock_send_envelope = self.socket.send_envelope = Mock()

        self.socket.send_obj(mock_obj)

        mock_serial = mock_obj.serialize.return_value
        mock_dumps.assert_called_with(mock_serial)
        mock_json_str = mock_dumps.return_value
        mock_envelope_cls.new.assert_called_with(
                'application/json', mock_json_str, id='')

        mock_envelope = mock_envelope_cls.new.return_value
        mock_send_envelope.assert_called_with(mock_envelope)

    def test_send_envelope(self):
        mock_envelope = Mock()
        self.socket.send_envelope(mock_envelope)
        self.mock_zmq_socket.send_multipart.assert_called_with(
                mock_envelope.transfer_object.return_value)

    @patch('dploylib.transport.wrapper.Envelope')
    def test_send_text(self, mock_envelope_cls):
        text = 'hello'
        mock_send_envelope = self.socket.send_envelope = Mock()

        self.socket.send_text(text)

        mock_envelope_cls.new.assert_called_with(TEXT_MIMETYPE, text, id='')
        mock_envelope = mock_envelope_cls.new.return_value
        mock_send_envelope.assert_called_with(mock_envelope)

    @patch('json.loads')
    def test_receive_obj(self, mock_loads):
        mock_handler = Mock()
        mock_recv_envelope = self.socket.receive_envelope = Mock()

        obj = self.socket.receive_obj(mock_handler)

        mock_envelope = mock_recv_envelope.return_value
        mock_loads.assert_called_with(mock_envelope.data)
        mock_json_str = mock_loads.return_value
        mock_handler.assert_called_with(mock_json_str)
        eq_(obj, mock_handler.return_value)

    @patch('dploylib.transport.wrapper.Envelope')
    def test_receive_envelope(self, mock_envelope_cls):
        self.socket.receive_envelope()
        self.mock_zmq_socket.recv_multipart.assert_called_with()

    def test_receive_text(self):
        mock_recv_envelope = self.socket.receive_envelope = Mock()
        mock_envelope = mock_recv_envelope.return_value
        mock_envelope.mimetype = TEXT_MIMETYPE
        text = self.socket.receive_text()

        eq_(text, mock_envelope.data)


def test_get_zmq_constant():
    # Just test a bunch of expected values
    tests = [
        ['pub', zmq.PUB],
        ['sub', zmq.SUB],
        ['rep', zmq.REP],
        ['req', zmq.REQ],
        ['router', zmq.ROUTER],
        ['dealer', zmq.DEALER],
        ['pull', zmq.PULL],
        ['push', zmq.PUSH],
        ['subscribe', zmq.SUBSCRIBE],
    ]
    for name, expected in tests:
        yield do_get_zmq_constant, name, expected


def do_get_zmq_constant(name, expected):
    constant = get_zmq_constant(name)
    eq_(constant, expected)


@raises(AttributeError)
def test_get_zmq_constant_fails():
    get_zmq_constant('thisissomekindofrandomnamethatwontbethere')
    get_zmq_constant('thisissomekindofrandomnamethatwontbethere')
