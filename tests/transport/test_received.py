from nose.tools import raises, eq_
from mock import Mock, patch
from dploylib.transport.received import *


class TestReceivedData(object):
    def setup(self):
        self.mock_envelope = Mock()
        self.mock_deserializer = Mock()
        self.received = ReceivedData(self.mock_envelope,
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
