from dploylib import services
from dploylib import servers
from dploylib.servers.generic import BroadcastServer


class SomeObject(object):
    pass


class BuildQueueServer(servers.Server):
    @servers.bind_in('request', 'rep', obj=SomeObject)
    def receive_request(self, socket, received):
        # This should be an instance of obj
        obj = received.obj
        # This is the raw envelope that was received
        received.envelope
        # This is the raw envelope that was received
        socket.send_obj(obj)


class ObservableWorkerBlueprint(object):
    broadcast = services.blueprint_server(BroadcastServer)
    queue = services.blueprint_server()


service = services.Service(
        coordinator=services.ThreadedServerCoordinator,
        extends=[ObservableWorkerBlueprint])

service.add_server('queue', BuildQueueServer)


if __name__ == '__main__':
    service.run()
