
DROP MATERIALIZED VIEW IF EXISTS cell_count_by_study_specimen CASCADE ;
DROP MATERIALIZED VIEW IF EXISTS marker_positive_cell_count_by_study_specimen CASCADE ;
DROP MATERIALIZED VIEW IF EXISTS composite_marker_positive_cell_count_by_study_specimen CASCADE ;

DROP VIEW IF EXISTS cells_count_criteria_satisfied CASCADE;
DROP VIEW IF EXISTS criterion_count CASCADE;
DROP VIEW IF EXISTS all_criteria_satisfied CASCADE;
DROP VIEW IF EXISTS generalized_marker_positive_cell_count_by_study_specimen CASCADE;
DROP VIEW IF EXISTS fraction_by_marker_study_specimen CASCADE;
DROP VIEW IF EXISTS fraction_stats_by_marker_study CASCADE;
DROP VIEW IF EXISTS fraction_stats_by_marker_study_assessment CASCADE;
