"""
tests.services.test_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests services.
"""
from mock import Mock, MagicMock, patch
from nose.tools import raises
from nose.plugins.attrib import attr
from dploylib.services.service import Service


def test_initialize_service():
    mock_template = Mock()
    mock_server = Mock()
    mock_config_mapper = Mock()

    service = Service(templates=[mock_template],
            config_mapper=mock_config_mapper)
    service.add_server('test', mock_server)


class TestBasicService(object):
    def setup(self):
        self.mock_template = Mock()
        self.mock_templates = [self.mock_template]
        self.mock_server = Mock()
        self.mock_config_mapper = Mock()
        self.mock_coordinator = Mock()

        self.settings_patch = patch('dploylib.services.service.Settings')
        self.mock_settings_cls = self.settings_patch.start()

        service = Service(templates=[self.mock_template],
                config_mapper=self.mock_config_mapper,
                coordinator=self.mock_coordinator)
        service.add_server('test', self.mock_server)
        self.service = service

        self.mock_server_config = self.service._server_config = MagicMock()

    def teardown(self):
        self.settings_patch.stop()

    def test_start(self):
        mock_coordinator = self.mock_coordinator
        fake_config = {
            'service': {
                'servers': {'test': 'testconfig'},
            },
        }
        self.service.start(fake_config)

        self.mock_server_config.apply_templates.assert_called_with(
                self.mock_templates)

        self.mock_config_mapper.process.assert_called_with(fake_config)
        mock_processed_config = self.mock_config_mapper.process.return_value
        mock_coordinator.setup_servers.assert_called_with(
                self.mock_server_config, mock_processed_config)
        mock_coordinator.start.assert_called_with()

    @raises(TypeError)
    def test_start_fails_no_config(self):
        self.service.start()

    def test_start_with_config_string(self):
        config_string = 'somestring'

        self.service.start(config_string=config_string)

        self.mock_config_mapper.process_string.assert_called_with(
                config_string)
        mock_processed_config = (self.mock_config_mapper.process_string
                .return_value)
        self.mock_coordinator.setup_servers.assert_called_with(
                self.mock_server_config, mock_processed_config)

    def test_start_with_config_dict(self):
        config_dict = dict(a='a')

        self.service.start(config_dict=config_dict)

        self.mock_settings_cls.assert_called_with(config_dict)
        mock_processed_config = self.mock_settings_cls.return_value
        self.mock_coordinator.setup_servers.assert_called_with(
                self.mock_server_config, mock_processed_config)
