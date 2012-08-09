from nose.tools import eq_, raises
from mock import Mock
from dploylib.services.utils import *


def mock_description(name, no_server=False):
    mock_description = Mock()
    mock_description.name = name
    if no_server:
        mock_description.server = None
    return mock_description


def assert_equal_sets(a, b, message='Sets not equal'):
    eq_(set(a), set(b), message)


class TestServerConfig(object):
    def setup(self):
        self.config = ServerConfig()

    def test_apply_templates_succeeds(self):
        mock_template1 = Mock()
        mock_template2 = Mock()
        mock_templates = [mock_template1, mock_template2]

        mock_description1 = mock_description('test1')
        mock_description2 = mock_description('test2')
        mock_description3 = mock_description('test3')

        mock_template1.server_descriptions.return_value = [
            mock_description1,
            mock_description2,
        ]
        mock_template2.server_descriptions.return_value = [
            mock_description3,
        ]

        self.config.apply_templates(mock_templates)
        server_names = self.config.names()

        mock_template1.server_descriptions.assert_called_with()
        mock_template2.server_descriptions.assert_called_with()

        assert_equal_sets(server_names, ['test1', 'test2', 'test3'])

    @raises(ServerConfigError)
    def test_apply_templates_fails(self):
        mock_template1 = Mock()
        mock_templates = [mock_template1]

        mock_description1 = mock_description('test1')
        mock_description2 = mock_description('test2', no_server=True)

        mock_template1.server_descriptions.return_value = [
            mock_description1,
            mock_description2,
        ]

        self.config.apply_templates(mock_templates)

    def test_apply_templates_succeeds_with_user_set_servers(self):
        mock_template1 = Mock()
        mock_templates = [mock_template1]

        mock_description1 = mock_description('test1')
        mock_description2 = mock_description('test2', no_server=True)

        mock_template1.server_descriptions.return_value = [
            mock_description1,
            mock_description2,
        ]

        self.config['test2'] = Mock()
        self.config['test3'] = Mock()

        self.config.apply_templates(mock_templates)

        server_names = self.config.names()

        assert_equal_sets(server_names, ['test1', 'test2', 'test3'])

    def test_iterate_servers(self):
        self.config['test1'] = Mock()
        self.config['test2'] = Mock()
        self.config['test3'] = Mock()

        names = []
        for name, server in self.config:
            names.append(name)

        assert_equal_sets(names, ['test1', 'test2', 'test3'])
