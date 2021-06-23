import re

import pandas as pd
import numpy as np

from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALORegionalAreasProvider:
    def __init__(
        self,
        dataset_design=None,
        regional_areas_file: str=None,
    ):
        self.dataset_design = dataset_design
        self.load_regional_areas(regional_areas_file)

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

        df = self.dataset_design.normalize_fov_descriptors(df)

        self.areas = {}
        for i, row in df.iterrows():
            for column, [compartment, units] in focus_columns.items():
                fov = row[self.dataset_design.get_FOV_column()]
                area = float(row[column])
                if not np.isnan(area):
                    self.areas[(fov, compartment)] = area

    def get_units(self, compartment: str=None):
        return self.units[compartment]

    def get_fov_compartments(self):
        return sorted(list(self.areas.keys()))

    def get_area(self, fov: str=None, compartment: str=None):
        if not (fov, compartment) in self.areas:
            return None
        return self.areas[(fov, compartment)]

    def get_total_compartmental_area(self, fov: str=None):
        accumulator = 0
        for [variable_fov, compartment], value in self.areas.items():
            if fov == variable_fov:
                accumulator += value
        if accumulator == 0:
            return None
        return accumulator
