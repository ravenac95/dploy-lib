"""
tests.servers.test_server
~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from nose.tools import eq_, raises
from nose.plugins.attrib import attr
from mock import Mock, patch, ANY, call
from dploylib.servers.server import *


class GenericServerTest(object):
    name = 'server'
    server_cls = None

    def setup(self):
        self.mock_settings = Mock()
        self.fake_control_uri = 'inproc://someproc'
        self.mock_context = Mock()
        self.poll_loop_patch = patch('dploylib.servers.server.PollLoop')
        self.mock_poll_loop = self.poll_loop_patch.start()

        self.server = self.server_cls.new(self.name, self.mock_settings,
                self.fake_control_uri, context=self.mock_context)

    def teardown(self):
        self.poll_loop_patch.stop()


@attr('medium')
class TestServerDescription(object):
    def setup(self):
        self.description_patch = patch(
                'dploylib.servers.server.SocketDescription',
                autospec=True)

        self.mock_description_cls = self.description_patch.start()

    def teardown(self):
        self.description_patch.stop()

    def test_iter_socket_descriptions(self):
        expected_descriptions = [
            ('receive_request', ANY),
            ('another_request', ANY),
        ]
        from dploylib import servers

        class FakeServerDescription(servers.Server):
            @servers.bind_in('reply', 'rep')
            def receive_request(self, socket, received):
                socket.send_envelope(received.envelope)

            @servers.bind_in('another', 'rep')
            def another_request(self, socket, received):
                socket.send_envelope(received.envelope)

        server_description = FakeServerDescription()

        iter_descs = server_description.iter_socket_descriptions()
        descriptions = []
        for name, description in iter_descs:
            assert (name, description) in expected_descriptions
            descriptions.append((name, description))

        self.mock_description_cls.assert_has_calls([
            call('reply', 'rep', 'bind', input_handler=ANY,
                deserializer=None),
            call('another', 'rep', 'bind', input_handler=ANY,
                deserializer=None),
        ])


class TestSocketDescription(object):
    def setup(self):
        self.mock_handler = Mock()
        self.mock_options = Mock()
        self.mock_deserializer = Mock()
        self.name = 'somename'
        self.socket_type = 'socket'
        self.setup_type = 'bind'
        self.socket_handler_wrapper_patch = patch(
                'dploylib.servers.server.SocketHandlerWrapper')
        self.mock_socket_handler_wrapper_cls = \
                self.socket_handler_wrapper_patch.start()
        self.description = SocketDescription(self.name, self.socket_type,
                self.setup_type, input_handler=self.mock_handler,
                deserializer=self.mock_deserializer,
                default_options=self.mock_options)

    def test_create_socket(self):
        mock_context = Mock()
        uri = 'uri'
        options = [
            ['abc', 'def'],
            ['123', 456],
        ]
        self.description.create_socket(mock_context, uri, options)

        mock_context.socket.assert_called_with(self.socket_type)
        mock_socket = mock_context.socket.return_value
        mock_socket.bind.assert_called_with(uri)

    def test_handler(self):
        mock_server = Mock()
        handler = self.description.handler(mock_server)
        self.mock_socket_handler_wrapper_cls.assert_called_with(mock_server,
                self.mock_handler, self.mock_deserializer)
        mock_wrapped_handler = (self.mock_socket_handler_wrapper_cls
                .return_value)
        eq_(handler, mock_wrapped_handler)


class TestSocketHandlerWrapper(object):
    def setup(self):
        self.mock_server = Mock()
        self.mock_handler = Mock()
        self.mock_deserializer = Mock()

        self.wrapper = SocketHandlerWrapper(self.mock_server,
                self.mock_handler,
                deserializer=self.mock_deserializer)

    @patch('dploylib.servers.server.SocketReceived')
    def test_call(self, mock_received_cls):
        mock_socket = Mock()

        self.wrapper(mock_socket)

        mock_socket.receive_envelope.assert_called_with()

        mock_envelope = mock_socket.receive_envelope.return_value

        mock_received_cls.assert_called_with(mock_envelope,
                self.mock_deserializer)

        self.mock_handler.assert_called_with(self.mock_server,
                mock_received_cls.return_value)


class TestSocketReceived(object):
    def setup(self):
        self.mock_envelope = Mock()
        self.mock_deserializer = Mock()
        self.received = SocketReceived(self.mock_envelope,
                self.mock_deserializer)

    @patch('json.loads')
    def test_get_json_data(self, mock_loads):
        self.mock_envelope.mimetype = 'application/json'
        json_data = self.received.json

        mock_loads.assert_called_with(self.mock_envelope.data)
        eq_(json_data, mock_loads.return_value)

    @patch('json.loads')
    def test_get_json_data_wrong_mimetype(self, mock_loads):
        json_data = self.received.json
        eq_(json_data, None)

    @patch('json.loads')
    def test_get_obj(self, mock_loads):
        self.mock_envelope.mimetype = 'application/json'
        obj = self.received.obj
        eq_(obj, self.mock_deserializer.deserialize.return_value)

    @raises(DataNotDeserializable)
    @patch('json.loads')
    def test_get_obj_raises_error(self, mock_loads):
        self.received.obj
