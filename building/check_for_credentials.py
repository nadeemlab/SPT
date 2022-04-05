#!/usr/bin/env python3
import configparser
import json
import os
from os.path import exists
from os.path import join
import sys


class CredentialChecker:
    def __init__(self):
        self.accounts = ['pypi', 'docker', 'github',]

    def found(self, account):
        print('\'found\'', end='')
        exit()

    def not_found(self, account):
        print('\'not_found\'', end='')
        exit()

    def check_for_credentials(self, account):
        if account == 'pypi':
            config = configparser.ConfigParser()
            pypirc = join(os.environ['HOME'], '.pypirc')
            if not exists(pypirc):
                self.not_found(account)
            config.read(pypirc)
            if not 'spatialprofilingtoolbox' in config.sections():
                self.not_found(account)
            fields = ['repository', 'username', 'password']
            if not all([x in config['spatialprofilingtoolbox'] for x in fields]):
                self.not_found(account)
            self.found(account)
        if account == 'docker':
            configfile = join(os.environ['HOME'], '.docker', 'config.json')
            if not exists(configfile):
                self.not_found(account)
            config = json.loads(open(configfile, 'rt').read())
            if not 'auths' in config:
                self.not_found(account)
            if len(config['auths'].keys()) == 0:
                self.not_found(account)
            self.found(account)

    def explain_arguments(self):
        print('Need to supply one of: %s' % str(self.accounts))
        exit(1)


if __name__=='__main__':
    checker = CredentialChecker()
    if len(sys.argv) < 2:
        checker.explain_arguments()
    account = sys.argv[1]
    if not account in checker.accounts:
        checker.explain_arguments()
    checker.check_for_credentials(account)

