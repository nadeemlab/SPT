
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.sample_stratification import SampleStratificationCreator as SSC


def test_is_convertible():
    def numeric_valuation(x):
        return float(x)

    assert SSC.is_convertible('123', numeric_valuation)
    assert SSC.is_convertible('000123', numeric_valuation)
    assert SSC.is_convertible('000.123', numeric_valuation)
    assert SSC.is_convertible('12x3', numeric_valuation) == False

def test_get_date_valuation():
    assert SSC.get_date_valuation(['2018-03-01', '2019-01-01', '2020-12-30']).__name__ == 'iso_valuation'
    assert SSC.get_date_valuation(['7', '8', '9']).__name__ == 'numeric_valuation'
    assert SSC.get_date_valuation(['descriptor A, timepoint 1', 'descriptor B, timepoint 2', 'descriptor C, timepoint 50']).__name__ == 'timepoint_extractor'
    assert SSC.get_date_valuation(['2018-03-01', '8', '9']) is None

def test_get_verbalization_of_interventional_position():
    interventions = [
        ('Intervention A', '2018-03-01'),
        ('Intervention B', '2019-01-01'),
        ('Intervention C', '2019-05-01'),
    ]

    v = SSC.get_verbalization_of_interventional_position(interventions, '2019-03-01')
    assert v == 'Between Intervention B, Intervention C'

    v = SSC.get_verbalization_of_interventional_position(interventions, '2018-03-02')
    assert v == 'Between Intervention A, Intervention B'

    v = SSC.get_verbalization_of_interventional_position(interventions, '2017-12-31')
    assert v == 'Before Intervention A'

    v = SSC.get_verbalization_of_interventional_position(interventions, '2019-06-01')
    assert v == 'After Intervention C'

def test_get_verbalization_of_diagnostic_state():
    diagnoses = [
        ('Diagnosis D', 'timepoint 2'),
        ('Diagnosis E', 'timepoint 4'),
        ('Diagnosis F', 'timepoint 7'),
    ]
    assert SSC.get_verbalization_of_diagnostic_state('timepoint 1', diagnoses) == 'Diagnosis D'
    assert SSC.get_verbalization_of_diagnostic_state('timepoint 2', diagnoses) == 'Diagnosis D'
    assert SSC.get_verbalization_of_diagnostic_state('timepoint 3', diagnoses) == 'Diagnosis E'
    assert SSC.get_verbalization_of_diagnostic_state('timepoint 4', diagnoses) == 'Diagnosis E'
    assert SSC.get_verbalization_of_diagnostic_state('timepoint 5', diagnoses) == 'Diagnosis F'
    assert SSC.get_verbalization_of_diagnostic_state('timepoint 6', diagnoses) == 'Diagnosis F'
    assert SSC.get_verbalization_of_diagnostic_state('timepoint 7', diagnoses) == 'Diagnosis F'
    assert SSC.get_verbalization_of_diagnostic_state('timepoint 8', diagnoses) == ''

if __name__=='__main__':
    test_is_convertible()
    test_get_date_valuation()
    test_get_verbalization_of_interventional_position()
    test_get_verbalization_of_diagnostic_state()
