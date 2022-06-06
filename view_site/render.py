#!/usr/bin/env python3
import jinja2
from jinja2 import Environment
from jinja2 import BaseLoader
jinja_environment = Environment(loader=BaseLoader)


if __name__ == '__main__':
    contents = open('index.html.jinja').read()
    template = jinja_environment.from_string(contents)
    index = template.render({'api_url': 'data.nadeemlabapi.link', 'protocol' : 'https'})
    with open('index.html', 'wt') as file:
        file.write(index)
    if not exists('host'):
        print('Warning: File "host" containing the IP address not found; can not create domain-free variant of webpage.')
        index_no_domain = index
    else:
        ip = open('host').read().rstrip()
        index_no_domain = template.render({'api_url': ip, 'protocol' : 'http'})
    with open('index_no_domain.html', 'wt') as file:
        file.write(index_no_domain)
