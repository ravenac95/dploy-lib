from nose.tools import eq_
from dploylib.transport.envelope import *


def test_create_envelope():
    envelope = Envelope.new('mimetype', 'data', id='id')
    eq_(envelope.mimetype, 'mimetype')
    eq_(envelope.data, 'data')
    eq_(envelope.id, 'id')


def test_create_envelope_from_raw():
    raw = ['id', 'mimetype', 'data']
    envelope = Envelope.from_raw(raw)
    eq_(envelope.mimetype, 'mimetype')
    eq_(envelope.data, 'data')
    eq_(envelope.id, 'id')


class TestEnvelope(object):
    def setup(self):
        self.envelope = Envelope('id', 'mimetype', 'data')

    def test_transfer_object(self):
        eq_(['id', 'mimetype', 'data'], self.envelope.transfer_object())
