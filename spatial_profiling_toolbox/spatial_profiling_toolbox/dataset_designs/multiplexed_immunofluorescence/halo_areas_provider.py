import re

import pandas as pd

from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALORegionalAreasProvider:
    def __init__(
        self,
        dataset_design=None,
        filename_lookup: (lambda x:None)=None,
    ):
        self.dataset_design = dataset_design
        file_identifier = dataset_design.get_regional_areas_file_identifier()
        file = filename_lookup(file_identifier)
        self.load_regional_areas(file)

    def load_regional_areas(self, file):
        df = pd.read_csv(file)

        compartments = '(' + '|'.join(self.dataset_design.get_compartments()) + ')'
        whitespace = ' +'
        units = '\((.+)\)'
        pattern = '^' + compartments + whitespace + '[Aa]rea' + whitespace + units + '$'
        focus_columns = {}
        for column in df.columns:
            match = re.search(pattern, column)
            if match:
                compartment = match.group(1)
                units = match.group(2)
                focus_columns[column] = [compartment, units]
                logger.debug(
                    'Found column "%s" containing areas of compartment "%s" in units "%s"',
                    column,
                    compartment,
                    units,
                )

        if len(focus_columns) == 0:
            logger.warning('No columns appeared in %s which could be interpreted as regional areas.', file)
            return

        self.units = {}
        for column, [compartment, units] in focus_columns.items():
            self.units[compartment] = units

        self.areas = {}
        for i, row in df.iterrows():
            for column, [compartment, units] in focus_columns.items():
                fov = row[self.dataset_design.get_FOV_column()]
                area = float(row[column])
                self.areas[(fov, compartment)] = area

    def get_area(
        self,
        fov: str=None,
        compartment: str=None,
    ):
        return self.areas[(fov, compartment)]

    def get_units(
        self,
        compartment: str=None,
    ):
        return self.units[compartment]

    def get_fov_compartments(self):
        return sorted(list(self.areas.keys()))
