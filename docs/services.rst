Services Library
================

Services are complete applications composed of multiple dploylib servers.

In order to facilitate flexibility services are setup, by default, to use a
YAML configuration to manage the servers that it runs. This configuration looks
like this::
    
    # Service configuration
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
    general:
      output-uri: *build-broadcast-in
