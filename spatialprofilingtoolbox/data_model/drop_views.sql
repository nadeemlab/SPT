
DROP MATERIALIZED VIEW IF EXISTS cell_count_by_study_specimen CASCADE ;
DROP MATERIALIZED VIEW IF EXISTS marker_positive_cell_count_by_study_specimen CASCADE ;
DROP MATERIALIZED VIEW IF EXISTS composite_marker_positive_cell_count_by_study_specimen CASCADE ;

DROP VIEW IF EXISTS cells_count_criteria_satisfied CASCADE;
DROP VIEW IF EXISTS criterion_count CASCADE;
DROP VIEW IF EXISTS all_criteria_satisfied CASCADE;
DROP VIEW IF EXISTS generalized_marker_positive_cell_count_by_study_specimen CASCADE;
DROP VIEW IF EXISTS fraction_by_marker_study_specimen CASCADE;
DROP VIEW IF EXISTS fraction_generalized_cases CASCADE;

DROP VIEW IF EXISTS fraction_moments_generalized_cases CASCADE;

DROP VIEW IF EXISTS fraction_extrema CASCADE;
DROP VIEW IF EXISTS fraction_arg_maxima CASCADE;
DROP VIEW IF EXISTS fraction_arg_minima CASCADE;

DROP MATERIALIZED VIEW IF EXISTS fraction_stats CASCADE;
