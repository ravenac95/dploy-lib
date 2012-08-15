# -*- coding: utf-8 -*-

"""
dploylib.services.config
~~~~~~~~~~~~~~~~~~~~~~~~

Handles configuration data for services.

Configuration data is accessed through a settings object. The Settings object
stores information as a specific hierarchy of data. This is the raw data stored
in the Settings object::

    {
        "servers": {
            "broadcast": { # Setting for the broadcast server, by socket name
                "in": { ... settings in socket ... }
                ...
            },
            "queue": {
                ... queue server settings ...
            },
            ...
        }
        "general": { # General settings are a simple key-value storage
            ... general settings ...
        }
    }

Settings objects are defined and used like this::

    >>> settings = Settings(data)

    # General settings are accessed like this
    >>> settings.get('some-settings')
    some_setting_value

    # Settings store socket information in a special way
    # This data is accessed like this
    >>> socket_info = settings.socket_info('some_server_name',
    ...     'some_socket_name')

    >>> print socket_info
    {'uri': 'some-uri', 'options': 'any-options-if-any'}

Settings can also be bound to a server via ServerSettings::

    >>> server_settings = settings.server_settings('server_name')
    # Server settings can still grab general settings with no problems
    >>> server_settings.get

    >>> socket_info = server_settings.socket_info('some_socket_name')

    >>> print socket_info
    {'uri': 'some-uri', 'options': 'any-options-if-any'}
"""

import yaml
from .. import constants


class ServerNotInConfiguration(Exception):
    pass


class SocketInfoNotInConfiguration(Exception):
    pass


class Undefined(object):
    pass
undefined = Undefined()


class ConfigMapper(object):
    """Maps configurations from various sources into a Settings object"""
    def process(self, config_data):
        raise NotImplementedError()


class YAMLConfigMapper(object):
    def process(self, config_path):
        """Loads data from a yaml file.

        :param config_data: Path to the configuration file
        """
        yaml_file = open(config_path, 'r')
        config_data = yaml.load(yaml_file)
        return Settings(config_data)


class ServerSettings(object):
    def __init__(self, server_name, settings):
        self._settings = settings
        self._server_name = server_name

    def get(self, key, default=undefined):
        return self._settings.get(key, default)

    def socket_info(self, socket_name):
        return self._settings.socket_info(self._server_name, socket_name)


class Settings(object):
    def __init__(self, data):
        self._data = data
        self._server_section = data[constants.SETTINGS_SERVER_SECTION]

    def get(self, key, default=undefined):
        """Get from general settings"""
        value = self._data[constants.SETTINGS_GENERAL_SECTION].get(key,
                default)
        if value is undefined:
            raise KeyError('"%s" not in general settings' % key)
        return value

    def socket_info(self, server_name, socket_name):
        server_info = self.server_info(server_name)
        socket_info = server_info.get(socket_name, None)
        if not socket_info:
            raise SocketInfoNotInConfiguration(
                    'Socket info for "%s" on server "%s" not included in '
                    'configuration' % (socket_name, server_name))
        return socket_info

    def server_info(self, server_name):
        server_info = self._server_section.get(server_name, None)
        if not server_info:
            raise ServerNotInConfiguration(
                    'Server "%s" not included in configuration' % server_name)
        return server_info

    def server_settings(self, server_name):
        # Verify the server exists
        self.server_info(server_name)
        # Create the settings
        return ServerSettings(server_name, self)
