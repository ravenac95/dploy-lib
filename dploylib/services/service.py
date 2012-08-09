import logging
from .utils import ServerConfig
from .coordinator import *
from .config import *


logger = logging.getLogger('dploylib.services.service')


class Service(object):
    """A facade to a DployService"""
    logger = logger

    def __init__(self, templates=None, config_mapper=None, coordinator=None):
        self._templates = templates or []
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

    def start(self, config_data):
        """Starts the service with a certain configuration data"""
        config_mapper = self._config_mapper
        coordinator = self._coordinator
        server_config = self.server_config

        server_names = server_config.names()
        self.logger.debug('Starting service with %d servers' %
                len(server_names))
        settings = config_mapper.process(config_data, servers=server_names)
        coordinator.setup_servers(server_config, settings)
        coordinator.start()

    def wait(self):
        try:
            self._coordinator.wait()
        except ServerCoordinatorFailing:
            self.logger.exception('Service is failing. Please stop now.')
            raise ServiceFailing('Service has stopped working')

    def stop(self):
        self._coordinator.stop()
