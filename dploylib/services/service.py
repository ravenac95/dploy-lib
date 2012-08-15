# -*- coding: utf-8 -*-

"""
dploylib.services.service
~~~~~~~~~~~~~~~~~~~~~~~~~

Defines the dploy service
"""

import logging
from .utils import ServerConfig
from .coordinator import *
from .config import *


logger = logging.getLogger('dploylib.services.service')


class Service(object):
    """The Service object provides a way to create a zeromq-based dploy
    service. In dploy, a the service object is in charge of a combination of
    :class:`~dploylib.servers.server.Server` objects. Each of the Server
    objects acts as a definition for a server which is used to spawn threads,
    processes, or greenlets of each server.

    :param templates: a list of service templates to apply to this service
    :param config_mapper: default YAMLConfigMapper, configuration mapper for
        the service
    :param coordinator: the server coordinator for the service. Defaults to
        :class:`~dploylib.services.coordinator.ThreadedServerCoordinator`
    """
    logger = logger

    def __init__(self, templates=None, config_mapper=None, coordinator=None):
        self._templates = templates or []
        self._server_config = ServerConfig()
        self._configuration_locked = False
        self._config_mapper = config_mapper or YAMLConfigMapper()
        self._coordinator = coordinator or ThreadedServerCoordinator()

    def add_server(self, name, server_cls):
        """Register a :class:`~dploylib.servers.server.Server` to the Service
        instance

        :param name: name of the server
        :param server_cls: A :class:`~dploylib.servers.server.Server`
        """
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
        """Starts the service with the given configuration information.
        Configuration data is accepted from one of three different types: *a
        file path*, *a string*, or *a dictionary*.

        :param config_file: file path for the configuration
        :param config_string: a string of the configuration
        :param config_dict: a dictionary for the configuration
        """
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
        """Wait for the service forever or until it fails"""
        try:
            self._coordinator.wait()
        except ServerCoordinatorFailing:
            self.logger.exception('Service is failing')
            raise ServiceFailing('Service has stopped working')

    def stop(self):
        """Stop the service"""
        self._coordinator.stop()
        self.logger.debug('Service stopped')

    def run(self, *args, **kwargs):
        """A default method for running a service"""
        self.start(*args, **kwargs)
        try:
            self.wait()
        except ServiceFailing:
            self.logger.debug('Stopping service')
        except KeyboardInterrupt:
            self.logger.debug('Service stopped by user')
        finally:
            self.stop()
