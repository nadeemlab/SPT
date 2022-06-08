#!/usr/bin/env python3
import os
from os.path import exists

import jinja2
from jinja2 import Environment
from jinja2 import BaseLoader
jinja_environment = Environment(loader=BaseLoader)


if __name__ == '__main__':
    contents = open('stats_viewing.js.jinja').read()
    template = jinja_environment.from_string(contents)
    stats_viewing = template.render({'api_url': 'data.nadeemlabapi.link', 'protocol' : 'https'})
    with open('stats_viewing.js', 'wt') as file:
        file.write(stats_viewing)
    if not exists('host'):
        print('Warning: File "host" containing the IP address not found; can not create domain-free variant of webpage.')
        stats_viewing_no_domain = stats_viewing
    else:
        ip = open('host').read().rstrip()
        stats_viewing_no_domain = template.render({'api_url': ip, 'protocol' : 'http'})
    with open('stats_viewing_no_domain.js', 'wt') as file:
        file.write(stats_viewing_no_domain)

    contents = open('index.html.jinja').read()
    template = jinja_environment.from_string(contents)
    index = template.render({'script_file': 'stats_viewing.js'})
    with open('index.html', 'wt') as file:
        file.write(index)

    index_no_domain = template.render({'script_file': 'stats_viewing_no_domain.js'})
    with open('index_no_domain.html', 'wt') as file:
        file.write(index_no_domain)
