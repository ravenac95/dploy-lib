.. _services-intro:

Getting started with services
=============================

The dploy stack is composed of a many separate services interacting with each
other. The majority of these services are built using zeromq as a transport the
rest are built using HTTP to communicate. Since HTTP has a plethora of tools
for creating related web services dploylib does not need to do much to aid that
process. However, ZeroMQ based services can be more complicated to implement.
The dploylib simplifies and unifies portions of this process through it's
concept of services.

What are services?
------------------

In dploy, services are complete applications composed of multiple dploy
servers. Each of these servers reacts to input events on various zeromq
sockets. 


Simple Echo Service
-------------------

The simplest way to understand services is to create a very simple service.
Let's start by creating a very simple echo service. 

Here is one of the simplest services you could define::
    
    from dploylib import servers
    from dploylib.services import Service

    class EchoServer(servers.Server):
        @servers.bind_in('request', 'rep')
        def echo_request(self, socket, received):
            socket.send_envelope(received)
    
    service = Service()
    service.add_server('echo', EchoServer)

    if __name__ == '__main__':
        config_dict = {
            "servers": {
                "echo": {
                    "request": {
                        "uri": "tcp://127.0.0.1:5000",
                    },
                },
            },
        }
        service.run(config_dict=config_dict)

To run simply do::
    
    $ python myservice.py

If you run the service you will be able to interact with it as follows::
    
    >>> from dploylib.transport import Socket
    >>> echo_socket = Socket.new('req', 'tcp://127.0.0.1:14445')
    >>> echo_socket.send_text('hello')
    >>> print echo_socket.receive_text()
    hello

Fantastic! You now have a working echo server.

If you can't tell, server and service definition was inspired by both flask and
django web development frameworks. Let's have a look at what just happened:

1. First we import :mod:`~dploylib.servers`. This import will allow us
   to create our echo server easily.
2. Next we import the :class:`~dploylib.services.Service` class. If you're
   familiar with flask, the service class is much like the Flask class in that
   it can be instantiated at the module level and run as an application later.
3. For the next few lines we define the ``EchoServer`` class. 
   
  a. The first line of the class makes it so we subclass from
     :class:`~dploylib.servers.Server`.
  b. The next line decorates the method ``echo_request``. The decorator
     :func:`~dploylib.servers.bind_in` provides instructions to the containing
     server class, ``EchoServer``. It tells the server class the following: 
       
     - Bind a zeromq ``REP`` socket named ``requests`` to the server
     - The ``_in`` suffix on the decorator means the decorated method is the
       socket's input handler

  c. Finally, within the method ``echo_request``, we define the echo server
     logic. It simply gets the data it receives and sends it back to the
     user. When using dploylib's sockets, data is received in a standard 
     envelope. This will be explained later.

4. The line starting with ``service =`` instantiates a Service object into the
   module's namespace. On the next line the EchoServer we defined on step 3 is
   registered to the service as a server named ``echo`` via the method
   ``add_server``.
5. A fake configuration is defined and set saved in ``config_dict``
6. Finally, the service is started by the method
   :meth:`~dploylib.services.Service.run`. It takes the fake
   configuration as the keyword argument, ``config_dict``.

To stop the server, use control-C.

Standard service configuration
------------------------------

One of the things that we don't want to do is hard code configuration. However,
in the previous example we hard coded the configuration into the 
``if __name__ == '__main__'`` block. Luckily, services are not meant to be used
in this way, although the facility is available for easy debugging or testing
if necessary. Let's do a better job by using configuration files that we can
change without touching any code.

dploy defines a standard configuration file that can is to be used with all
services. The basic structure is able to translate to a multitude of
configuration languages, but YAML is chosen by default due to it's writability,
readability and portability to other languages.

Here is a basic configuration:

.. code-block:: yaml
    
    servers:  # Server configurations
      echo:   # Config for "echo" server
        request:   # Config for "echo" server's "request" socket
          uri: tcp://127.0.0.1:14445  # URI for "request" socket

    # General configuration
    general:
      someconfig1: somevalue1
      someconfig2: somevalue2
