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

    service = Service(extends=[mock_blueprint], config_mapper=mock_config_mapper)
    service.add_server('test', mock_server)


class TestBasicService(object):
    def setup(self):
        self.mock_blueprint = Mock()
        self.mock_server = Mock()
        self.mock_config_mapper = Mock()

        service = Service(extends=[self.mock_blueprint],
                config_mapper=self.mock_config_mapper)
        service.add_server('test', self.mock_server)
        self.service = service

    def test_start(self):
        fake_config = {
            'service': {
                'servers': {'test': 'testconfig'},
            },
        }
        mock_process_blueprints = self.service.process_blueprints = Mock()
        self.service.start(fake_config)

        self.mock_config_mapper.process.assert_called_with(fake_config, servers=['test'])
