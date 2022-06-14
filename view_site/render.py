#!/usr/bin/env python3
import jinja2
from jinja2 import Environment
from jinja2 import BaseLoader
jinja_environment = Environment(loader=BaseLoader)


class NetworkEnvironmentProvider:
    @classmethod
    def get_template_dict(cls):
        return {
            'host_ip' : cls.get_host_ip(),
            'api_url' : cls.get_api_url(),
            'protocol' : cls.get_protocol(),
        }

    @classmethod
    def get_host_ip(cls):
        return open('host_ip').read().rstrip()

    @classmethod
    def get_api_url(cls):
        pass

    @classmethod
    def get_protocol(cls):
        pass


class AnonymousNetworkEnvironmentProvider(NetworkEnvironmentProvider):
    @classmethod
    def get_api_url(cls):
        return cls.get_host_ip()

    @classmethod
    def get_protocol(cls):
        return 'http'


class DomainNamedNetworkEnvironmentProvider(NetworkEnvironmentProvider):
    @classmethod
    def get_api_url(cls):
        return 'data.nadeemlabapi.link'

    @classmethod
    def get_protocol(cls):
        return 'https'


if __name__ == '__main__':
    template_input = open('index.html.jinja').read()
    template = jinja_environment.from_string(template_input)
    target_file_providers = {
        'index.html' : DomainNamedNetworkEnvironmentProvider,
        'index_no_domain.html' : AnonymousNetworkEnvironmentProvider,
    }
    for index_file, EnvironmentProvider in target_file_providers.items():
        contents = template.render(EnvironmentProvider.get_template_dict())
        with open(index_file, 'wt') as file:
            file.write(contents)

