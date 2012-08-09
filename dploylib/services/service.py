class ThreadedServerCoordinator(object):
    pass


class ConfigMapper(object):
    pass


class Service(object):
    """A facade to a DployService"""
    def __init__(self, extends=None, config_mapper=None, coordinator=None):
        self._extends = extends or []
        self._server_classes = {}
        self._config_mapper = config_mapper or ConfigMapper()
        self._coordinator = coordinator or ThreadedServerCoordinator()

    def add_server(self, name, server_cls):
        self._server_classes[name] = server_cls

    def process_blueprints(self):
        pass

    def start(self, config):
        """Starts the service with a certain configuration"""
        config_mapper = self._config_mapper
        server_classes = self._server_classes
        coordinator = self._coordinator

        server_names = server_classes.keys()
        config_mapper.process(config, servers=server_names)
