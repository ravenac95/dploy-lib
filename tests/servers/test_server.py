"""
tests.servers.test_server
~~~~~~~~~~~~~~~~~~~~~~~~~

Server setup is inspired by flask and flask blueprints.


The syntax::

    from dploylib import servers


    some_server = servers.Server()

    # Bind a socket but don't listen for it's input
    some_server.bind('pub', name='publish')

    # Bind a socket and use a method to listen for incoming data
    @some_server.bind_in('pull')
    def receive_message(server, socket, envelope):
        pass


    @some_server.bind_in('rep') # Bind's a REP or a REQ-REP
    def receive_queue(server, socket, envelope):
        pass


    #### You can also define a generic server ####

    class BroadcastServer(servers.Server):
        # Bind a socket but don't listen for it's input. Useful for output
        publish = server.bind('pub', name='out')

        @servers.bind_in('pull', name='in')
        def receive_message(self, socket, envelope):
            self.sockets.publish.send_envelope(envelope)

    class QueueServer(servers.Server):
        @servers.bind_in('rep', name='request')
        def receive_request(self, socket, envelope):
            object = self.handle_queue(envelope)k
            socket.send_obj(object)

    class ObservableWorkerService(services.Service):
        broadcast = services.add_server(BroadcastServer)
        queue = services.add_server(QueueServer)

    service = ObservableWorkerService('build')

YAML config::
    # Service configuration
    service:
      servers:
        broadcast:
          in:
            uri: &build-broadcast-in
              inproc://broadcast-in
            options:
              - ['hwm', 1000]
          out:
            uri: tcp://127.0.0.1:9991
        queue:
          request:
            uri: tcp://127.0.0.1:9992

    # General configuration
    settings:
      output-uri: *build-broadcast-in
"""
