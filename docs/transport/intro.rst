Why create a wrapper?
=====================

``dploylib.transport`` sets up the custom transport library used by
dploy. This custom transport library is simply a wrapper around zeromq. The
main purpose of creating the wrapper is to allow for the usage of dploy's
:class:`~dploylib.transport.Envelope`. This envelope will allow for greater
extension later as well as allowing the transport layer to be replaced if we
ever need it. The main impetus for creating a wrapper is the inclusion of an
encryption layer later down the line. However, the wrapper is also able to
simplify the usage of zeromq in any particular application.

The wrapper tries to stay as close to the original API of pyzqm as possible.
This is to prevent the need to learn much more than the zeromq guide provides.

Simple REQ-REP echo server
--------------------------

Here's the REP server ``server.py``::
    
    from dploylib.transport import Context

    def main():
        context = Context.new()
        socket = context.socket('rep')
        socket.bind('tcp://127.0.0.1:5555')

        while True:
            text = socket.receive_text()
            socket.send_text(text)

    if __name__ == '__main__':
        main()

Now the REQ server in ``client.py``::
    
    from dploylib.transport import Context

    def main():
        context = Context.new()
        socket = context.socket('req')
        socket.connect('tcp://127.0.0.1:5555')

        socket.send_text('hello')
        text = socket.receive_text()

        print text

    if __name__ == '__main__':
        main()

First run the server in one process::
    
    $ python server.py

Then run the client and you should see this::
    
    $ python client.py
    hello

All of zeromq's socket types are available.
