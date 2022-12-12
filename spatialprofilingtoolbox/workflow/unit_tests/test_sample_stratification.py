
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

def test_get_interventional_position():
    interventions = [
        ('Intervention A', '2018-03-01'),
        ('Intervention B', '2019-01-01'),
        ('Intervention C', '2019-05-01'),
    ]
    assert SSC.get_interventional_position(interventions, '2017-12-31') == ['Before', 'Intervention A', '2018-03-01']
    assert SSC.get_interventional_position(interventions, '2018-03-02') == ['After', 'Intervention A', '2018-03-01']
    assert SSC.get_interventional_position(interventions, '2019-03-01') == ['After', 'Intervention B', '2019-01-01']
    assert SSC.get_interventional_position(interventions, '2019-06-01') == ['After', 'Intervention C', '2019-05-01']

def test_get_diagnostic_state():
    diagnoses = [
        ('Diagnosis D', 'Positive', 'timepoint 2'),
        ('Diagnosis E', 'Positive', 'timepoint 4'),
        ('Diagnosis F', 'Negative', 'timepoint 7'),
    ]
    assert SSC.get_diagnostic_state('timepoint 1', diagnoses) == ['Diagnosis D', 'Positive', 'timepoint 2']
    assert SSC.get_diagnostic_state('timepoint 2', diagnoses) == ['Diagnosis D', 'Positive', 'timepoint 2']
    assert SSC.get_diagnostic_state('timepoint 3', diagnoses) == ['Diagnosis E', 'Positive', 'timepoint 4']
    assert SSC.get_diagnostic_state('timepoint 4', diagnoses) == ['Diagnosis E', 'Positive', 'timepoint 4']
    assert SSC.get_diagnostic_state('timepoint 5', diagnoses) == ['Diagnosis F', 'Negative', 'timepoint 7']
    assert SSC.get_diagnostic_state('timepoint 6', diagnoses) == ['Diagnosis F', 'Negative', 'timepoint 7']
    assert SSC.get_diagnostic_state('timepoint 7', diagnoses) == ['Diagnosis F', 'Negative', 'timepoint 7']
    assert SSC.get_diagnostic_state('timepoint 8', diagnoses) == ['', '', '']

if __name__=='__main__':
    test_is_convertible()
    test_get_date_valuation()
    test_get_interventional_position()
    test_get_diagnostic_state()
