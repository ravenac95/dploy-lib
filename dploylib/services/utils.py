class ServerConfigError(Exception):
    pass


class ServerConfig(object):
    def __init__(self):
        self._servers = {}

    def apply_templates(self, templates):
        """Apply's the templates the settings"""
        servers = self._servers
        for template in templates:
            server_descriptions = template.server_descriptions()
            for description in server_descriptions:
                template_server = description.server
                name = description.name
                actual_server = servers.setdefault(name, template_server)
                if not actual_server:
                    raise ServerConfigError('ServerConfig requires server '
                            'named "%s"' % name)

    def __getitem__(self, name):
        return self._servers[name]

    def __setitem__(self, name, server):
        self._servers[name] = server

    def names(self):
        return self._servers.keys()

    def __iter__(self):
        return self._servers.iteritems()
