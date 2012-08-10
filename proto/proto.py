from dploylib import services
from dploylib import servers
from dploylib.servers.generic import BroadcastServer


class SomeObject(object):
    pass


class BuildQueueServer(servers.Server):
    @servers.bind_in('request', 'rep', obj=SomeObject)
    def receive_request(self, socket, received):
        # This should be an instance of obj given that obj is provided to
        # bind_in
        obj = received.obj
        # This is the raw envelope that was received
        received.envelope
        socket.send_obj(obj)


class ObservableWorkerTemplate(object):
    broadcast = services.blueprint_server(BroadcastServer)
    queue = services.blueprint_server()


service = services.Service(templates=[ObservableWorkerTemplate])

service.add_server('queue', BuildQueueServer)


if __name__ == '__main__':
    service.run()
