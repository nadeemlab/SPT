import os
from os.path import exists
from os.path import abspath
import re
import json

from ...environment.configuration_settings import workflows
from ...environment.configuration_settings import config_filename
from ...environment.configuration_settings import get_version


class DialogSolicitor:
    def print(self, message, *args, fill_colors='magenta', end='\n'):
        """
        :param message: A message to display to the user.
        :type message: str

        :param args: String tokens to fill in appearances of '%s' in ``message``.

        :param fill_colors: Single color name or list of color names for the special
            strings.

        :param end: Convenience argument in CLI case. Similar to ``end`` argument of
            the usual ``print`` function.
        :type end: str
        """
        pass

    def prompt(self, message, *args, fill_colors='magenta', validator=None):
        """
        :param message: A prompt message to display to the user.
        :type message: str

        :param args: String tokens to fill in appearances of '%s' in ``message``.

        :param fill_colors: Single color name or list of color names for the special
            strings.

        :param validator: Dictionary with 'checker' function and 'otherwise' string.
        :type validator: dict
        """
        pass

    def show_list(self, entries):
        """
        Tells the interface to show the user a list of option descriptions or names.

        :param entries: List of possible options pertaining to upcoming prompt.
        :type entries: list
        """
        pass


class CLI(DialogSolicitor):
    green='\u001b[32m'
    boldgreen='\u001b[1;32m'
    magenta='\u001b[35m'
    boldmagenta='\u001b[1;35m'
    cyan='\u001b[36m'
    boldcyan='\u001b[1;36m'
    yellow='\u001b[33m'
    boldyellow='\u001b[1;33m'
    red='\u001b[31m'
    bold_red='\u001b[31;1m'
    blue='\u001b[34m'
    reset='\u001b[0m'
    cr='\u001b[F'
    upline='\u001b[A'

    def print(self, message, *args, fill_colors='magenta', end='\n'):
        if isinstance(fill_colors, str):
            colors = [self.__getattribute__(fill_colors)] * len(args)
        else:
            colors = [self.__getattribute__(c) for c in fill_colors]

        tokens = message.split('%s')
        tokens = [self.yellow + token + self.reset for token in tokens]
        message = '%s'.join(tokens)
        for i in range(len(args)):
            arg = args[i]
            color = colors[i]
            message = re.sub('%s', color + arg + self.reset, message, 1)
        print(message, end = end)

    def prompt(self, message, *args, fill_colors='magenta', validator=None):
        self.print(message, *args, fill_colors=fill_colors, end=' ')
        response = input()
        if not validator is None:
            while not validator['checker'](response):
                self.print(' %s', validator['otherwise'], fill_colors='red')
                self.print(message, *args, fill_colors=fill_colors, end=' ')
                response = input()
        return response

    def show_list(self, entries):
        for entry in entries:
            self.print(' %s', entry, fill_colors='cyan')


def configuration_dialog(source: DialogSolicitor=CLI()):
    """
    :param source: Default ``CLI()`` (i.e. command line interface). If desired you
        can supply an alternative implementation of the interface
        ``DialogSolicitor``.
    :type source: DialogSolicitor
    """
    pp = source

    if exists(config_filename):
        pp.print("Configuration file %s already exists.", config_filename)
        exit()

    parameters = {}

    pp.print('')
    pp.print(' spt_version %s', get_version(), fill_colors='boldcyan')
    pp.print(' %s', 'https://github.com/nadeemlab/SPT', fill_colors='blue')
    pp.print('')
    pp.print('This dialog solicits parameters for your SPT pipeline run and generates a JSON')
    pp.print('configuration file.')
    pp.print('')

    workflow_names = sorted(list(workflows.keys()))
    pp.print('Workflows:')
    pp.show_list(workflow_names)
    parameters['workflow'] = pp.prompt(
        'Enter the computational workflow type:',
        validator = {
            'checker' : (lambda w: w in workflow_names),
            'otherwise' : 'Choose a valid workflow name.',
        },
    )

    yes_pattern = '([yY]|[yY]es)'
    no_pattern = '([nN]|[nN]o)'
    bool_validator = {
        'checker' : lambda response: re.match(yes_pattern, response) or re.match(no_pattern, response),
        'otherwise' : 'Enter y or n.',
    }

    path_validator = {
        'checker' : lambda path: exists(path),
        'otherwise' : 'Path does not exist.',
    }

    parameters['input_path'] = pp.prompt(
        'Enter the path containing input CSV files pertaining to cells:',
        validator=path_validator,
    )
    parameters['input_path'] = abspath(parameters['input_path'])

    parameters['file_manifest_file'] = pp.prompt(
        'Enter the file manifest file:',
    )

    compartments = pp.prompt(
        'Enter comma-separated list of compartment names:',
    )
    if compartments != '':
        compartments_list = [compartment.strip() for compartment in compartments.split(',')]
        parameters['compartments'] = sorted(compartments_list)

    from spatialprofilingtoolbox.workflows.phenotype_proximity import components
    workflow_name = list(components.keys())[0]
    if parameters['workflow'] == workflow_name:
        balanced = pp.prompt(
            'Balanced/symmetric analysis with respect to phenotype pairs?',
            validator = bool_validator,
        )
        if re.match(yes_pattern, balanced):
            balanced = True
        else:
            balanced = False
        parameters['balanced'] = balanced

    from spatialprofilingtoolbox.workflows.density import components
    workflow_name = list(components.keys())[0]
    if parameters['workflow'] == workflow_name:
        use_intensities = pp.prompt(
            'Use intensity weighting?',
            validator = bool_validator,
        )
        if re.match(yes_pattern, use_intensities):
            use_intensities = True
        else:
            use_intensities = False
        parameters['use_intensities'] = use_intensities

    from spatialprofilingtoolbox.workflows.diffusion import components
    workflow_name = list(components.keys())[0]
    if parameters['workflow'] == workflow_name:
        save_graphml = pp.prompt(
            'Save GraphML represetation of diffusion distances for every phenotype mask?',
            validator = bool_validator,
        )
        if re.match(yes_pattern, save_graphml):
            save_graphml = True
        else:
            save_graphml = False
        parameters['save_graphml'] = save_graphml

    skip_integrity_check = pp.prompt(
        'Skip file integrity check?',
        validator = bool_validator,
    )
    if re.match(yes_pattern, skip_integrity_check):
        skip_integrity_check = True
    else:
        skip_integrity_check = False
    parameters['skip_integrity_check'] = skip_integrity_check

    parameters = {**parameters}

    parameters['spt_version'] = get_version()

    json_string = json.dumps(parameters, indent=4) + '\n'
    open(config_filename, 'wt').write(json_string)
    pp.print('Wrote %s .', config_filename)
    pp.print('Contents:')
    pp.print('')
    print(json_string)
