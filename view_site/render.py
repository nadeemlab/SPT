#!/usr/bin/env python3
import os
from os.path import exists

import jinja2
from jinja2 import Environment
from jinja2 import BaseLoader
jinja_environment = Environment(loader=BaseLoader)


if __name__ == '__main__':
    ip = open('host').read().rstrip()

    contents = open('stats_viewing.js.jinja').read()
    stats_viewing_template = jinja_environment.from_string(contents)
    stats_viewing = stats_viewing_template.render({'api_url': 'data.nadeemlabapi.link', 'protocol' : 'https'})
    with open('stats_viewing.js', 'wt') as file:
        file.write(stats_viewing)
    stats_viewing_no_domain = stats_viewing_template.render({'api_url': ip, 'protocol' : 'http'})
    with open('stats_viewing_no_domain.js', 'wt') as file:
        file.write(stats_viewing_no_domain)

    contents = open('index.html.jinja').read()
    index_template = jinja_environment.from_string(contents)
    index = index_template.render({'script_file': 'stats_viewing.js', 'host' : ip, 'api_url': 'data.nadeemlabapi.link', 'protocol' : 'https'})
    with open('index.html', 'wt') as file:
        file.write(index)
    index_no_domain = index_template.render({'script_file': 'stats_viewing_no_domain.js', 'host' : ip, 'api_url': ip, 'protocol' : 'http'})
    with open('index_no_domain.html', 'wt') as file:
        file.write(index_no_domain)
