"""Test presence of fractions features and assessments of them."""
import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker

if __name__=='__main__':
    with DatabaseConnectionMaker(database_config_file='../db/.spt_db.config.container') as dcm:
        connection = dcm.get_connection()
        specification = pd.read_sql('SELECT * FROM feature_specification', connection)
        specifier = pd.read_sql('SELECT * FROM feature_specifier', connection)
        value_assignment = pd.read_sql('SELECT * FROM quantitative_feature_value', connection)

        print(specification.to_string())
        print(specifier.to_string())
        print(value_assignment.to_string())
