#!/bin/bash

FOUND_VERSION_CHANGE='no'
FOUND_ANOTHER_CHANGE='no'

status=$(git status -s |
{
while IFS= read -r line
  do
    is_modified_file=$(echo "$line" | grep -oE '^ ?M')
    if [[ "$is_modified_file" == ' M' || "$is_modified_file" == 'M' ]]; then
        if [[ "$line" == ' M spatialprofilingtoolbox/version.txt' ]]; then
            FOUND_VERSION_CHANGE=1
        else
            FOUND_ANOTHER_CHANGE=1
        fi
    fi

    is_added_file=$(echo "$line" | grep -oE '^A[M ] ')
    if [[ "$is_added_file" != "" ]]; then
        FOUND_ANOTHER_CHANGE=1
    fi
done

if [[ ( "$FOUND_VERSION_CHANGE" == "1" ) && ( "$FOUND_ANOTHER_CHANGE" == "1" ) ]]; then
    echo "11"
fi

if [[ ( "$FOUND_VERSION_CHANGE" == "0" ) ]]; then
    echo "0x"
fi
})

if [[ "$status" == "11" ]];
then
    logstyle-printf "$red""Version has changed, but found another change. Not ready to autorelease.$reset"
    exit
fi

if [[ "$status" == "0x" ]];
then
    logstyle-printf "$red""Version has not changed, so not ready to autorelease.$reset"
    logstyle-printf "$yellow""Maybe you need one last commit?$reset"
    exit
fi



#!/usr/bin/env python3
import configparser
import json
import os
from os.path import exists
from os.path import join
import sys


class CommitStateChecker:
    def __init__(self):

    def all_committed(self):
        print('1', end='')
        exit()

    def some_changed(self):
        print('0', end='')
        exit()

    def check_for_committed_source(self):
        if account == 'pypi':
            config = configparser.ConfigParser()
            pypirc = join(os.environ['HOME'], '.pypirc')
            if not exists(pypirc):
                self.not_found()
            config.read(pypirc)
            if not 'spatialprofilingtoolbox' in config.sections():
                self.not_found()
            fields = ['repository', 'username', 'password']
            if not all([x in config['spatialprofilingtoolbox'] for x in fields]):
                self.not_found()
            self.found()
        if account == 'docker':
            configfile = join(os.environ['HOME'], '.docker', 'config.json')
            if not exists(configfile):
                self.not_found()
            config = json.loads(open(configfile, 'rt').read())
            if not 'auths' in config:
                self.not_found()
            if len(config['auths'].keys()) == 0:
                self.not_found()
            key = list(config['auths'].keys())[0]
            if not 'auth' in config['auths'][key]:
                self.not_found()
            self.found()

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

