from .utils import ServerConfig


class ThreadedServerCoordinator(object):
    pass


class YAMLConfigMapper(object):
    pass


class Service(object):
    """A facade to a DployService"""
    def __init__(self, extends=None, config_mapper=None, coordinator=None):
        self._templates = extends or []
        self._server_config = ServerConfig()
        self._configuration_locked = False
        self._config_mapper = config_mapper or YAMLConfigMapper()
        self._coordinator = coordinator or ThreadedServerCoordinator()

    def add_server(self, name, server_cls):
        self._server_config[name] = server_cls

    def _apply_templates(self):
        self._server_config.apply_templates(self._templates)
        self._configuration_locked = True

    @property
    def server_config(self):
        if not self._configuration_locked:
            self._apply_templates()
            return self._server_config
        return self._server_config

    def start(self, config):
        """Starts the service with a certain configuration"""
        config_mapper = self._config_mapper
        coordinator = self._coordinator
        server_config = self.server_config

        server_names = server_config.names()
        processed_config = config_mapper.process(config, servers=server_names)
        coordinator.setup_servers(server_config, processed_config)
        coordinator.start()

    def wait(self):
        self._coordinator.wait()

    def stop(self):
        self._coordinator.stop()
