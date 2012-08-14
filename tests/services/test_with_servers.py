from nose.tools import eq_
from testkit import MultiprocessTest, ProcessWrapper
from dploylib import servers
from dploylib.services import Service
from dploylib.transport import *


class EchoServer(servers.Server):
    @servers.bind_in('request', 'rep')
    def echo_request(self, socket, received):
        socket.send_envelope(received.envelope)


class EchoServerProcess(ProcessWrapper):
    def setup(self, shared_options):
        service = Service()
        service.add_server('echo', EchoServer)
        self.service = service
        self.service_config = shared_options['service_config']
        self.service.start(config_dict=self.service_config)

    def run(self):
        self.service.wait()

    def teardown(self):
        self.service.stop()


class PubServer(servers.Server):
    out = servers.bind('out', 'pub')

    @servers.bind_in('in', 'pull')
    def pub_in(self, socket, received):
        self.sockets.out.send_envelope(received.envelope)


class TestEchoServerSetup(MultiprocessTest):
    wrappers = [EchoServerProcess]

    timeout = 2.0

    def shared_options(self):
        echo_uri = "tcp://127.0.0.1:14445"
        echo_config = {
            "servers": {
                "echo": {
                    "request": dict(uri=echo_uri),
                },
            },
        }
        self.context = Context.new()
        self.socket = self.context.socket('req')
        self.socket.connect(echo_uri)
        return dict(service_config=echo_config)

    def test_echo(self):
        self.socket.send_text('hello')
        eq_(self.socket.receive_text(), 'hello')
