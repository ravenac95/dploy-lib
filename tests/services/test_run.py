from mock import Mock
from nose.plugins.attrib import attr
from dploylib.services.config import Settings
from dploylib.services import Service

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


class FakeServer(object):
    @classmethod
    def new(cls, name, settings, control_uri, context=None):
        server = cls(name, settings, control_uri, context)
        server.connect_to_control()
        return server

    def __init__(self, name, settings, control_uri, context):
        self._context = context
        self._name = name
        self._settings = settings
        self._control_uri = control_uri
        self._control_socket = None

    def start(self):
        self._control_socket.receive_text()
        print 'Server "%s" all finished!' % self._name

    def connect_to_control(self):
        control_uri = self._control_uri
        control_socket = self._context.socket('sub')
        control_socket.set_option('subscribe', '')
        control_socket.connect(control_uri)
        self._control_socket = control_socket


@attr('large')
class TestServiceRunWithThreads(object):
    def setup(self):
        mock_config_mapper = Mock()
        mock_config_mapper.process.return_value = Settings(FAKE_SETTINGS_DATA)

        self.service = Service(config_mapper=mock_config_mapper)

    def test_single_server(self):
        self.service.add_server('broadcast', FakeServer)
        self.service.start(None)
        self.service.stop()

    def test_mulitple_servers(self):
        self.service.add_server('broadcast', FakeServer)
        self.service.add_server('queue', FakeServer)
        self.service.start(None)
        self.service.stop()
