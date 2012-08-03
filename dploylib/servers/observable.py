"""
dploylib.servers.observable
~~~~~~~~~~~~~~~~~~~~~~~~~~~

ObservableWorkerServer. This is a server that has two major components:

    1. A queue to queue work requests
    2. A broadcaster to publish the process of the worker as it occurs

To use just subclass ObservableWorkerServer as follows::

    class MyServer(ObservableWorkerServer):
        queue = QueueServer
        broadcast = BroadcastServer

And to start just do this::

    MyServer.run(config)

The configuration will be passed directly to the queue and broadcast classes.
"""
