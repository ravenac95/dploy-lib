from nose.tools import eq_
from mock import Mock, patch
from dploylib.services.config import *


class TestYAMLConfigMapper(object):
    def setup(self):
        self.config_mapper = YAMLConfigMapper()

    @patch('yaml.load')
    @patch('__builtin__.open')
    @patch('dploylib.services.config.Settings')
    def test_process(self, mock_settings_cls, mock_open, mock_load):
        mock_data = Mock()
        mock_settings = self.config_mapper.process(mock_data)

        mock_load.assert_called_with(mock_open.return_value)
        mock_settings_cls.assert_called_with(mock_load.return_value)

        eq_(mock_settings, mock_settings_cls.return_value)


FAKE_SETTINGS_DATA = {
    'servers': {
        'broadcast': {  # Setting for the broadcast server, by socket name
            'in': dict(uri='broadcast')
        },
        'queue': {
            'request': dict(uri='broadcast')
        },
    },
    'general': {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
    }
}


class TestSettings(object):
    def setup(self):
        self.settings = Settings(FAKE_SETTINGS_DATA)

    def test_get(self):
        tests = [
            ['key1', 'value1'],
            ['key2', 'value2'],
            ['key3', 'value3'],
        ]
        for key, value in tests:
            yield self.do_get, key, value

    def do_get(self, key, expected):
        eq_(self.settings.get(key), expected)

    def test_get_with_default(self):
        key = 'somekey'
        default = 'default'
        eq_(default, self.settings.get(key, default))

    def test_server_info(self):
        expected_server_info = FAKE_SETTINGS_DATA['servers']['broadcast']

        server_info = self.settings.server_info('broadcast')

        eq_(server_info, expected_server_info)

    def test_socket_info(self):
        expected_socket_info = FAKE_SETTINGS_DATA['servers']['broadcast']['in']
        socket_info = self.settings.socket_info('broadcast', 'in')
        eq_(socket_info, expected_socket_info)

    def test_server_settings(self):
        expected_socket_info = FAKE_SETTINGS_DATA['servers']['broadcast']['in']

        server_settings = self.settings.server_settings('broadcast')

        socket_info = server_settings.socket_info('in')
        eq_(socket_info, expected_socket_info)
