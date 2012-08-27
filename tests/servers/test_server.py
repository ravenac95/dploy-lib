"""
tests.servers.test_server
~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from nose.tools import eq_
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


class TestServerDescription(object):
    def setup(self):
        self.description_patch = patch(
                'dploylib.servers.server.SocketDescription',
                autospec=True)

        self.mock_description_cls = self.description_patch.start()

        from dploylib import servers

        class FakeServerDescription(servers.Server):
            def setup(self):
                pass

            @servers.bind_in('reply', 'rep')
            def receive_request(self, socket, received):
                socket.send_envelope(received.envelope)

            @servers.bind_in('another', 'rep')
            def another_request(self, socket, received):
                socket.send_envelope(received.envelope)

        self.server_description = FakeServerDescription()

    def teardown(self):
        self.description_patch.stop()

    def test_iter_socket_descriptions(self):
        expected_descriptions = [
            ('receive_request', ANY),
            ('another_request', ANY),
        ]

        iter_descs = self.server_description.iter_socket_descriptions()
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

    @patch('dploylib.servers.server.DployServer', autospec=True)
    def test_create_server(self, mock_dploy_server_cls):
        server_name = Mock()
        settings = Mock()
        control_uri = Mock()
        context = Mock()

        server_description = self.server_description
        mock_iter = server_description.iter_socket_description = Mock()
        mock_iter.return_value = []

        server_description.create_server(server_name, settings,
                control_uri, context)

        mock_dploy_server = mock_dploy_server_cls.new.return_value
        mock_dploy_server.add_setup.assert_called_with(
                server_description.setup.im_func)


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

    def teardown(self):
        self.socket_handler_wrapper_patch.stop()

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

    @patch('dploylib.servers.server.ReceivedData')
    def test_call(self, mock_received_cls):
        mock_socket = Mock()

        self.wrapper(mock_socket)

        mock_socket.receive_envelope.assert_called_with()

        mock_envelope = mock_socket.receive_envelope.return_value

        mock_received_cls.assert_called_with(mock_envelope,
                self.mock_deserializer)

        self.mock_handler.assert_called_with(self.mock_server,
                mock_socket, mock_received_cls.return_value)


class TestSocketHandlerWrapperWithHandler(object):
    def setup(self):
        self.mock_server = Mock()
        self.mock_deserializer = Mock()

        self.call_inspector = call_inspector = Mock()

        class FakeHandler(Handler):
            socket_type = 'rep'

            def __call__(self, server, socket, received):
                call_inspector(server, socket, received)

        self.wrapper = SocketHandlerWrapper(self.mock_server,
                FakeHandler(), deserializer=self.mock_deserializer)

    @patch('dploylib.servers.server.ReceivedData')
    def test_call(self, mock_received_cls):
        mock_socket = Mock()

        self.wrapper(mock_socket)

        self.call_inspector.assert_called_with(self.mock_server, mock_socket,
                mock_received_cls.return_value)


class TestDployServer(object):
    def setup(self):
        self.mock_settings = Mock()
        self.server_name = 'name'
        self.control_uri = 'uri'
        self.mock_context = Mock()

        self.mock_poll_loop = Mock()

        self.socket_storage_patch = patch(
                'dploylib.servers.server.SocketStorage')
        self.mock_socket_storage_cls = self.socket_storage_patch.start()
        self.mock_socket_storage = self.mock_socket_storage_cls.return_value

        self.server = DployServer(self.server_name, self.mock_settings,
                self.control_uri, self.mock_context,
                poll_loop=self.mock_poll_loop)

    def teardown(self):
        self.socket_storage_patch.stop()

    def test_add_socket(self):
        name = 'name'
        mock_socket = Mock()
        mock_handler = Mock()
        self.server.add_socket(name, mock_socket, mock_handler)

        self.mock_poll_loop.register.assert_called_with(mock_socket,
                mock_handler)
        self.mock_socket_storage.register.assert_called_with(name, mock_socket)

    def test_start(self):
        self.mock_poll_loop.poll.side_effect = ServerStopped

        self.server.start()

        self.mock_poll_loop.poll.assert_called_with()

    def test_add_setup(self):
        mock_setup_func = Mock()
        self.server.add_setup(mock_setup_func)

        mock_setup_func.assert_called_with(self.server)


def test_storage():
    storage = SocketStorage()
    storage.register('somename', 'socket')
    eq_(storage.somename, 'socket')
