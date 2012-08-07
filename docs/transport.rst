The transport library
=====================

The ``dploylib.transport`` sets up the custom transport library used by
dploy. This custom transport library is simply a wrapper around zeromq. The
main purpose of creating the wrapper is to allow for the usage of dploy's
custom messaging envelope. This envelope will allow for greater extension
later.

Using the library is almost the same as using zeromq.

Simple REQ-REP echo server
--------------------------

Here's the REP server::
    
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

Now the REQ server::
    
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

All of zeromq's socket types are available.
        
