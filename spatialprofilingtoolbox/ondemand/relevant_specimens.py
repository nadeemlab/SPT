"""Common access to a query for specimens."""

def relevant_specimens_query():
    return '''
        SELECT DISTINCT sdmp.specimen FROM specimen_data_measurement_process sdmp
        JOIN study_component sc1 ON sc1.component_study=sdmp.study
        JOIN study_component sc2 ON sc1.primary_study=sc2.primary_study
        JOIN feature_specification fsn ON fsn.study=sc2.component_study
        WHERE fsn.identifier=%s
    '''
