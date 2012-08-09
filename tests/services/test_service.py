"""
tests.services.test_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests services.
"""
from mock import Mock
from dploylib.services.service import Service


def test_initialize_service():
    mock_blueprint = Mock()
    mock_server = Mock()
    mock_config_mapper = Mock()

    service = Service(extends=[mock_blueprint],
            config_mapper=mock_config_mapper)
    service.add_server('test', mock_server)


class TestBasicService(object):
    def setup(self):
        self.mock_blueprint = Mock()
        self.mock_blueprints = [self.mock_blueprint]
        self.mock_server = Mock()
        self.mock_config_mapper = Mock()
        self.mock_coordinator = Mock()

        service = Service(extends=[self.mock_blueprint],
                config_mapper=self.mock_config_mapper,
                coordinator=self.mock_coordinator)
        service.add_server('test', self.mock_server)
        self.service = service

    def test_start(self):
        mock_coordinator = self.mock_coordinator
        fake_config = {
            'service': {
                'servers': {'test': 'testconfig'},
            },
        }
        mock_server_config = self.service._server_config = Mock()
        self.service.start(fake_config)

        mock_server_config.apply_blueprints.assert_called_with(
                self.mock_blueprints)

        self.mock_config_mapper.process.assert_called_with(fake_config,
                servers=mock_server_config.names.return_value)
        mock_processed_config = self.mock_config_mapper.process.return_value
        mock_coordinator.setup_servers.assert_called_with(
                mock_server_config, mock_processed_config)
        mock_coordinator.start.assert_called_with()
