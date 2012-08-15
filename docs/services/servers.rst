Servers Library
===============

Server setup for dploy-lib is inspired by heavily by flask. The syntax looks
like this::

    from dploylib import servers

    class BroadcastServer(servers.Server):
        # Bind a socket but don't listen for it's input. Useful for output
        publish = servers.bind('pub', name='out')

        @servers.bind_in('pull', name='in')
        def receive_message(self, socket, envelope):
            self.sockets.publish.send_envelope(envelope)

    class QueueServer(servers.Server):
        @servers.bind_in('rep', name='request')
        def receive_request(self, socket, envelope):
            object = self.handle_queue(envelope)k
            socket.send_obj(object)
