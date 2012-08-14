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

    def start(self, config_file=None, config_string=None, config_dict=None):
        """Starts the service with a certain configuration data"""
        if not (config_file or config_string or config_dict):
            raise TypeError('One of config_file, config_string or config_dict'
                    ' is required')
        config_mapper = self._config_mapper
        coordinator = self._coordinator
        server_config = self.server_config

        server_names = server_config.names()
        self.logger.debug('Starting service with %d server(s).' %
                len(server_names))
        if config_file:
            settings = config_mapper.process(config_file)
        if config_string:
            settings = config_mapper.process_string(config_string)
        if config_dict:
            settings = Settings(config_dict)
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
        self.logger.debug('Service stopped.')
