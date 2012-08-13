"""
tests.transport.test_sockets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These tests test that the sockets do as expected. It utilizes multiprocesses,
hopefully that doesn't break nose.
"""
import multiprocessing
import random
from Queue import Empty
from nose.tools import eq_
from nose.plugins.attrib import attr
from testkit import timeout
from dploylib.transport import Socket


class SocketTestServerError(Exception):
    pass


class ClientNeverSynchronized(Exception):
    pass


class GenericSocketTestServer(object):
    socket_type = None

    @classmethod
    def new_process(cls, sync_event, queue, options):
        server = cls(options)
        address = server.setup_socket('tcp://127.0.0.1')
        queue.put(address)
        if sync_event.wait(30.0):
            server.run()
        else:
            raise ClientNeverSynchronized()

    def setup_socket(self, address):
        server_socket = Socket.new(self.socket_type)
        port = server_socket.bind_to_random(address)
        self.server_socket = server_socket
        return '%s:%s' % (address, port)

    def run(self):
        raise NotImplementedError('Need server logic')

    def __init__(self, options):
        self.options = options


class GenericSocketTest(object):
    # This must be a GenericSocketTestServer
    socket_server = None
    timeout = 3
    auto_sync = True

    def setup_server(self):
        queue = multiprocessing.Queue()
        sync_event = multiprocessing.Event()
        options = self.setup_server_options()
        server_process = multiprocessing.Process(
                target=self.socket_server.new_process,
                args=[sync_event, queue, options])
        server_process.start()
        self.server_process = server_process
        self.queue = queue
        # Wait at most 3 seconds for something
        self.server_uri = self.get_from_queue_or_error(
                'Cannot get uri from server')
        self.sync_event = sync_event
        if self.auto_sync:
            self.synchronize_with_server()

    def synchronize_with_server(self):
        self.sync_event.set()

    def teardown_server(self):
        self.server_process.terminate()

    def setup(self):
        self.setup_server()

    def teardown(self):
        self.teardown_server()

    def setup_server_options(self):
        return {}

    def get_from_queue_or_error(self, error='Timed out waiting for queue'):
        try:
            data = self.queue.get(self.timeout)
        except Empty:
            self.server_process.terminate()
            raise SocketTestServerError(error)
        return data


class SimpleDataObject(object):
    """A simple object that can be serialized and deserialized"""
    def __init__(self, data):
        self.data = data

    def serialize(self):
        return {'data': self.data}

    @classmethod
    def deserialize(cls, obj):
        data = obj['data']
        return cls(data)


class SimpleRepServer(GenericSocketTestServer):
    socket_type = 'rep'

    def run(self):
        """Simple Echo"""
        server_socket = self.server_socket

        while True:
            envelope = server_socket.receive_envelope()
            server_socket.send_envelope(envelope)


@attr('large')
class TestSimpleRepReq(GenericSocketTest):
    """A Simple Rep Req server"""
    socket_server = SimpleRepServer

    @timeout(5.0)
    def test_make_text_request(self):
        text = 'hello'
        req_socket = Socket.connect_new('req', self.server_uri)
        req_socket.send_text(text)

        received_text = req_socket.receive_text()
        eq_(received_text, text)

    @timeout(5.0)
    def test_make_obj_request(self):
        obj = SimpleDataObject('hello')
        req_socket = Socket.connect_new('req', self.server_uri)
        req_socket.send_obj(obj)

        received_obj = req_socket.receive_obj(SimpleDataObject.deserialize)
        eq_(received_obj.data, 'hello')


class SimplePubServer(GenericSocketTestServer):
    socket_type = 'pub'

    def run(self):
        """A random set of publisher messages to publish"""
        messages = self.options['messages']
        id = self.options['id']
        for message in messages:
            self.server_socket.send_text(message, id=id)
        self.server_socket.send_text('---end---', id=id)


class GenericPubSubTest(GenericSocketTest):
    auto_sync = False

    def setup_server_options(self):
        self.messages = self.random_messages()
        self.id = self.random_string()
        return dict(id=self.id, messages=self.messages)

    def random_messages(self):
        random_length = random.choice(range(20)) + 1
        messages = []
        for i in range(random_length):
            message = self.random_string()
            messages.append(message)
        return messages

    def random_string(self):
        random_length = random.choice(range(20)) + 1
        chars = []
        for i in range(random_length):
            random_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            chars.append(random_char)
        string = ''.join(chars)
        return string


@attr('large')
class TestSimplePubSub(GenericPubSubTest):
    socket_server = SimplePubServer

    @timeout(5.0)
    def test_receive_text_messages(self):
        # Connect to the socket
        sub_socket = Socket.connect_new('sub', self.server_uri, [
            ['subscribe', self.id]
        ])
        # Synchronize
        self.synchronize_with_server()
        # Assert received messages
        received_messages = []
        while True:
            received = sub_socket.receive_text()
            if received == '---end---':
                break
            received_messages.append(received)
        eq_(received_messages, self.messages)


class ObjectPubServer(GenericSocketTestServer):
    socket_type = 'pub'

    def run(self):
        """A random set of publisher messages to publish"""
        messages = self.options['messages']
        id = self.options['id']
        for message in messages:
            obj = SimpleDataObject(message)
            self.server_socket.send_obj(obj, id=id)
        end_obj = SimpleDataObject('---end---')
        self.server_socket.send_obj(end_obj, id=id)


@attr('large')
class TestObjectPubSub(GenericPubSubTest):
    socket_server = ObjectPubServer

    @timeout(5.0)
    def test_receive_text_messages(self):
        # Connect to the socket
        sub_socket = Socket.connect_new('sub', self.server_uri, [
            ['subscribe', self.id],
        ])
        # Synchronize
        self.synchronize_with_server()
        # Assert received messages
        received_messages = []
        while True:
            received = sub_socket.receive_obj(SimpleDataObject.deserialize)
            if received.data == '---end---':
                break
            received_messages.append(received.data)
        eq_(received_messages, self.messages)
