
DROP MATERIALIZED VIEW IF EXISTS cell_count_by_study_specimen CASCADE ;
DROP MATERIALIZED VIEW IF EXISTS marker_positive_cell_count_by_study_specimen CASCADE ;

DROP VIEW IF EXISTS fraction_stats_by_marker_study CASCADE ;
DROP VIEW IF EXISTS fraction_by_marker_study_specimen CASCADE ;


--Below are to be deprecated
DROP MATERIALIZED VIEW IF EXISTS phenotyping_breakdown_report ;
DROP MATERIALIZED VIEW IF EXISTS single_channel_diagnosis_breakdown_report ;
DROP MATERIALIZED VIEW IF EXISTS single_channel_all_diagnosis_breakdown_report ;
DROP MATERIALIZED VIEW IF EXISTS composite_diagnosis_breakdown_report ;
DROP MATERIALIZED VIEW IF EXISTS composite_all_diagnosis_breakdown_report ;
