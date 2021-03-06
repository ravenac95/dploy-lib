from nose.plugins.attrib import attr
from nose.tools import eq_
from testkit import MultiprocessTest, ProcessWrapper, random_string
from dploylib import servers
from dploylib.services import Service
from dploylib.transport import *

# FIXME NEED TO RANDOMLY GENERATE THESE
ECHO_URI = 'tcp://127.0.0.1:14445'
PUB_IN_URI = 'tcp://127.0.0.1:14446'
PUB_OUT_URI = 'tcp://127.0.0.1:14447'
ROUTING_URI = 'tcp://127.0.0.1:14448'

FAKE_CONFIG = {
    "servers": {
        "echo": {
            "request": dict(uri=ECHO_URI),
        },
        "broadcast": {
            "in": dict(uri=PUB_IN_URI),
            "out": dict(uri=PUB_OUT_URI),
        },
        "router": {
            "request": dict(uri=ROUTING_URI),
        }
    },
}


class ServerProcess(ProcessWrapper):
    servers = []

    def setup(self, shared_options):
        service = Service()
        for server_name, server in self.servers:
            service.add_server(server_name, server)
        self.service = service
        self.service_config = shared_options['service_config']
        self.service.start(config_dict=self.service_config)

    def run(self):
        self.service.wait()

    def teardown(self):
        self.service.stop()


class EchoServer(servers.Server):
    @servers.bind_in('request', 'rep')
    def echo_request(self, socket, received):
        socket.send_envelope(received.envelope)


class EchoClassHandler(servers.Handler):
    socket_type = 'rep'

    def __call__(self, server, socket, received):
        socket.send_envelope(received.envelope)


class DoubleEchoServer(servers.Server):
    @servers.bind_in('request', 'rep')
    def double_echo(self, socket, received):
        envelope = self.double(received.envelope)
        socket.send_envelope(envelope)

    def double(self, envelope):
        data = envelope.data * 2
        return Envelope(id=envelope.id, mimetype=envelope.mimetype, data=data)


class EchoClassServer(servers.Server):
    echo_handler = EchoClassHandler.bind('request')


class EchoServerProcess(ServerProcess):
    servers = [
        ('echo', EchoServer),
    ]


class DoubleEchoServerProcess(ServerProcess):
    servers = [
        ('echo', DoubleEchoServer),
    ]


class EchoClassServerProcess(ServerProcess):
    servers = [
        ('echo', EchoClassServer),
    ]


class PubServer(servers.Server):
    out = servers.bind('out', 'pub')

    @servers.bind_in('in', 'pull')
    def pub_in(self, socket, received):
        self.sockets.out.send_envelope(received.envelope)


class PubServerProcess(ServerProcess):
    servers = [
        ('broadcast', PubServer),
    ]


class RoutingServer(servers.Server):
    @servers.bind_in('request', 'router')
    def request_received(self, socket, received):
        socket.send_envelope(received.envelope)


class RoutingServerProcess(ServerProcess):
    servers = [
        ('router', RoutingServer),
    ]


@attr('large')
class TestEchoServerSetup(MultiprocessTest):
    wrappers = [EchoServerProcess]

    timeout = 2.0

    def shared_options(self):
        self.context = Context.new()
        self.socket = self.context.socket('req')
        self.socket.connect(ECHO_URI)
        return dict(service_config=FAKE_CONFIG)

    def test_echo(self):
        for i in range(10):
            random_message = random_string(20)
            self.socket.send_text(random_message)
            eq_(self.socket.receive_text(), random_message)


@attr('large')
class TestEchoClassServerSetup(MultiprocessTest):
    wrappers = [EchoClassServerProcess]

    timeout = 2.0

    def shared_options(self):
        self.context = Context.new()
        self.socket = self.context.socket('req')
        self.socket.connect(ECHO_URI)
        return dict(service_config=FAKE_CONFIG)

    def test_echo(self):
        for i in range(10):
            random_message = random_string(20)
            self.socket.send_text(random_message)
            eq_(self.socket.receive_text(), random_message)


@attr('large')
class TestPubServerSetup(MultiprocessTest):
    wrappers = [PubServerProcess]

    timeout = 2.0

    def shared_options(self):
        self.random_id = random_string(10)
        self.context = Context.new()

        self.in_socket = self.context.socket('push')
        self.in_socket.connect(PUB_IN_URI)

        self.out_socket = self.context.socket('sub')
        self.out_socket.set_option('subscribe', self.random_id)
        self.out_socket.connect(PUB_OUT_URI)

        return dict(service_config=FAKE_CONFIG)

    def test_pub_echo(self):
        for i in range(10):
            random_message = random_string(20)
            self.in_socket.send_text(random_message, id=self.random_id)
            eq_(self.out_socket.receive_text(), random_message)


@attr('large')
class TestRoutingServer(MultiprocessTest):
    wrappers = [RoutingServerProcess]

    timeout = 2.0

    def shared_options(self):
        self.context = Context.new()
        self.socket = self.context.socket('req')
        self.socket.connect(ROUTING_URI)
        return dict(service_config=FAKE_CONFIG)

    def test_echo(self):
        for i in range(10):
            random_message = random_string(20)
            self.socket.send_text(random_message)
            eq_(self.socket.receive_text(), random_message)


@attr('large')
class TestDoubleEchoServer(MultiprocessTest):
    wrappers = [DoubleEchoServerProcess]

    timeout = 2.0

    def shared_options(self):
        self.context = Context.new()
        self.socket = self.context.socket('req')
        self.socket.connect(ECHO_URI)
        return dict(service_config=FAKE_CONFIG)

    def test_echo(self):
        for i in range(10):
            random_message = random_string(20)
            self.socket.send_text(random_message)
            eq_(self.socket.receive_text(), random_message * 2)
