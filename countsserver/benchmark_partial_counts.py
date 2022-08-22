#!/usr/bin/env python3
import time
import random
import re
import subprocess

import spatialprofilingtoolbox
from spatialprofilingtoolbox.environment.counts_service import CountRequester


def infer_default_address():
    help_text = subprocess.check_output('./spt-counts-server --help', shell=True, universal_newlines=True)
    lines = help_text.split('\n')
    address = {}
    for line in lines[1:]:
        if re.search('--host HOST', line):
            key = 'host'
        if re.search('--port PORT', line):
            key = 'port'
        match = re.search(r'\(default: ([\w\d\-\.]+)\)', line)
        if match:
            address[key] = match.group(1)
    return (address['host'], int(address['port']))


if __name__=='__main__':
    fixed_cases = [
        ['CD3'],
        ['CD3', 'CD4'],
        ['DAPI', 'CD20', 'KI67', 'LAG3'],
        ['DAPI', 'CD20', 'CD3', 'CD68'],
        ['B2M', 'MHCI', 'PD1', 'PDL1', 'CD25', 'CD27'],
        ['CD20', 'CD3', 'CD68'],
        ['DAPI', 'CD3', 'CD68'],
        ['DAPI', 'CD20', 'CD68'],
        ['DAPI', 'CD20', 'CD3'],
        ['MHCI', 'PD1', 'PDL1', 'CD25', 'CD27'],
        ['B2M', 'PD1', 'PDL1', 'CD25', 'CD27'],
        ['B2M', 'MHCI', 'PDL1', 'CD25', 'CD27'],
        ['B2M', 'MHCI', 'PD1', 'CD25', 'CD27'],
        ['B2M', 'MHCI', 'PD1', 'PDL1', 'CD27'],
        ['B2M', 'MHCI', 'PD1', 'PDL1', 'CD25'],
    ]
    all_channel_names = ['B2M', 'B7H3', 'CD14', 'CD163', 'CD20', 'CD25', 'CD27', 'CD3', 'CD4', 'CD56', 'CD68', 'CD8', 'DAPI', 'FOXP3', 'IDO1', 'KI67', 'LAG3', 'MHCI', 'MHCII', 'MRC1', 'PD1', 'PDL1', 'S100B', 'SOX10', 'TGM2', 'TIM3']
    study_name = 'Melanoma intralesional IL2 (Hollmann lab) - specimen collection'
    host, port = infer_default_address()

    tic = time.perf_counter()
    for case in fixed_cases:
        with CountRequester(host, port) as requester:
            counts = requester.get_counts(case, study_name)
        count = sum(counts.values())
        print('%s %s' % ('{:14}'.format(str(count)), ' '.join(case)))
    toc = time.perf_counter()
    print('Completed %s count actions in %s' % (len(fixed_cases), f'{toc - tic:0.4f} seconds'))
    per_second = len(fixed_cases) / (toc - tic)
    print('That is %s per second.' % per_second)
    print('')

    for size in range(1, len(all_channel_names)):
        trials = 10
        print('Randomly sampling %s channels %s times then querying for structure count.' % (size, trials))
        tic = time.perf_counter()
        for i in range(trials):
            case = list(random.sample(all_channel_names, size))
            with CountRequester(host, port) as requester:
                counts = requester.get_counts(case, study_name)
            count = sum(counts.values())
            print('%s %s' % ('{:14}'.format(str(count)), ' '.join(case)))
        toc = time.perf_counter()
        per_second = trials / (toc - tic)
        print('%s per second.' % per_second)
        print('')
