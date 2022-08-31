import configparser
import json
import os
from os.path import exists
from os.path import join
import sys


class CredentialChecker:
    def __init__(self):
        self.accounts = ['pypi', 'docker']
        self.checkers = {
            'pypi' : self.check_for_pypi_credentials,
            'docker' : self.check_for_docker_credentials,
        }
        self.result = None

    def explain_arguments(self):
        print('Need to supply one of: %s' % str(self.accounts))
        exit(1)

    def report_result(self):
        print('%s' % self.result, end='')
        exit()

    def check_for_credentials(self, account):
        checker = self.checkers[account]
        if checker():
            self.result = 'found'
        else:
            self.result = 'not_found'

    def check_for_pypi_credentials(self):
        config = configparser.ConfigParser()
        pypirc = join(os.environ['HOME'], '.pypirc')
        if not exists(pypirc):
            return False
        config.read(pypirc)
        if not 'spatialprofilingtoolbox' in config.sections():
            return False
        fields = ['repository', 'username', 'password']
        if not all([x in config['spatialprofilingtoolbox'] for x in fields]):
            return False
        return True

    def check_for_docker_credentials(self):
        configfile = join(os.environ['HOME'], '.docker', 'config.json')
        if not exists(configfile):
            return False
        config = json.loads(open(configfile, 'rt').read())
        if not 'auths' in config:
            return False
        if len(config['auths'].keys()) == 0:
            return False
        return True


if __name__=='__main__':
    checker = CredentialChecker()
    if len(sys.argv) < 2:
        checker.explain_arguments()
    account = sys.argv[1]
    if not account in checker.accounts:
        checker.explain_arguments()
    checker.check_for_credentials(account)
    checker.report_result()
