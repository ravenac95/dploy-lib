from mock import Mock, call
from dploylib.services.coordinator import *


class GenericServerCoordinatorTest(object):
    server_coordinator_cls = None

    def setup(self):
        self.mock_context = Mock()
        self.mock_server1 = mock_server1 = Mock()
        self.mock_server2 = mock_server2 = Mock()

        self.fake_control_uri = 'test'

        self.mock_server_config = [
            ['server1', mock_server1],
            ['server2', mock_server2],
        ]
        self.mock_settings = Mock()
        self.coordinator = self.server_coordinator_cls(
                control_uri=self.fake_control_uri,
                context=self.mock_context)
        self.coordinator.setup_servers(self.mock_server_config,
                self.mock_settings)


class TestFakeServerCoordinator(GenericServerCoordinatorTest):
    @property
    def server_coordinator_cls(self):
        class FakeServerCoordinator(ServerCoordinator):
            """A server coordinator we can use for testing"""
            spawner = Mock()
            start_server = Mock()

            start_control_socket = Mock(name='start_control_socket')
        return FakeServerCoordinator

    def test_start(self):
        coordinator = self.coordinator

        coordinator.start()

        mock_server_settings = self.mock_settings.server_settings.return_value

        coordinator.spawner.assert_has_calls([
            call(target=coordinator.start_server,
                args=(self.mock_server1, 'server1', mock_server_settings,
                    self.fake_control_uri),
                kwargs=dict(context=self.mock_context),
            ),
            call().start(),
            call(target=coordinator.start_server,
                args=(self.mock_server2, 'server2', mock_server_settings,
                    self.fake_control_uri),
                kwargs=dict(context=self.mock_context),
            ),
            call().start()
        ])
        coordinator.start_control_socket.assert_called_with()
