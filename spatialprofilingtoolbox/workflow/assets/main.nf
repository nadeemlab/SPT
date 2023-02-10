
nextflow.enable.dsl = 2

process echo_environment_variables {
    output:
    path 'workflow',                        emit: workflow
    path 'file_manifest_filename',          emit: file_manifest_filename
    path 'input_path',                      emit: input_path
    path 'study_file',                      emit: study_file
    path 'diagnosis_file',                  emit: diagnosis_file
    path 'interventions_file',              emit: interventions_file
    path 'outcomes_file',                   emit: outcomes_file
    path 'db_config_file',                  emit: db_config_file
    path 'subjects_file',                   emit: subjects_file

    script:
    """
    #!/bin/bash
    echo -n "${workflow_}" > workflow
    echo -n "${file_manifest_filename_}" > file_manifest_filename
    echo -n "${input_path_}" > input_path
    echo -n "${study_file_}" > study_file
    echo -n "${diagnosis_file_}" > diagnosis_file
    echo -n "${interventions_file_}" > interventions_file
    echo -n "${outcomes_file_}" > outcomes_file
    echo -n "${db_config_file_}" > db_config_file
    echo -n "${subjects_file_}" > subjects_file
    echo -n "${channels_file_}" > channels_file
    echo -n "${phenotypes_file_}" > phenotypes_file
    """
}

process generate_run_information {
    input:
    val workflow
    path file_manifest_file
    val input_path
    path outcomes_file

    output:
    path 'job_specification_table.csv',     emit: job_specification_table

    script:
    """
    spt workflow generate-run-information \
     --use-file-based-data-model \
     --workflow='${workflow}' \
     --file-manifest-file=${file_manifest_file} \
     --input-path='${input_path}' \
     --outcomes-file=${outcomes_file} \
     --job-specification-table=job_specification_table.csv
    """
}

process workflow_initialize {
    input:
    val workflow
    path file_manifest_file
    path channels_file
    path phenotypes_file
    path outcomes_file
    path db_config_file
    path subjects_file
    path cell_manifest_files
    path study
    path diagnosis
    path interventions

    output:
    stdout                                  emit: initialization_flag

    script:
    """
    spt workflow initialize \
     --workflow='${workflow}' \
     --file-manifest-file=${file_manifest_file} \
     --outcomes-file=${outcomes_file}
     --database-config-file=${db_config_file}
     --subjects-file=${subjects_file}
     --study-file=${study} \
     --diagnosis-file=${diagnosis} \
     --interventions-file=${interventions} \
     --elementary-phenotypes-file=${channels_file} \
     --composite-phenotypes-file=${phenotypes_file}
    echo "Success"
    """
}

process core_job {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 4

    input:
    val initialization_flag
    val workflow
    tuple val(input_file_identifier), file(input_filename), val(job_index), val(outcome), val(sample_identifier)
    path channels
    path phenotypes

    output:
    path "metrics${job_index}.db",          emit: metrics_database
    path "metrics${job_index}.csv",         emit: performance_report

    script:
    """
    echo "Initialization status: ${initialization_flag}"
    spt workflow core-job \
     --workflow='${workflow}' \
     --input-file-identifier='${input_file_identifier}' \
     --input-filename=${input_filename} \
     --sample-identifier='${sample_identifier}' \
     --outcome='${outcome}' \
     --elementary-phenotypes-file=${channels} \
     --composite-phenotypes-file=${phenotypes} \
     --metrics-database-filename=metrics${job_index}.db
    """
}

process report_run_configuration {
    publishDir 'results'

    input:
    path all_cell_manifests
    val workflow
    path file_manifest_file
    path outcomes_file
    path channels
    path phenotypes

    output:
    path "run_configuration.log"

    script:
    """
    spt workflow report-run-configuration \
     --workflow='${workflow}' \
     --file-manifest-file=${file_manifest_file} \
     --outcomes-file=${outcomes_file}
     --elementary-phenotypes-file=${channels} \
     --composite-phenotypes-file=${phenotypes} >& run_configuration.log
    """
}

process merge_databases {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 6

    publishDir 'results'

    input:
    path all_metrics_databases

    output:
    path 'metrics_database.db',             emit: metrics_database

    script:
    """
    spt workflow merge-sqlite-dbs ${all_metrics_databases} --output=metrics_database.db
    """
}

process merge_performance_reports {
    publishDir 'results'

    input:
    path all_performance_reports

    output:
    path 'performance_report.md'

    script:
    """
    spt workflow merge-performance-reports ${all_performance_reports} --output=performance_report.md
    """
}

process aggregate_results {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 6

    publishDir 'results'

    input:
    path metrics_database
    path db_config_file
    path file_manifest_file
    val workflow
    path channels
    path phenotypes

    output:
    file 'stats_tests.csv'

    script:
    """
    spt workflow aggregate-core-results \
     --workflow='${workflow}' \
     --file-manifest-file=${file_manifest_file} \
     --metrics-database-filename=${metrics_database} \
     --database-config-file=${db_config_file}
     --elementary-phenotypes-file=${channels} \
     --composite-phenotypes-file=${phenotypes} \
     --stats-tests-file=stats_tests.csv
    """
}

workflow {
    echo_environment_variables()
        .set{ environment_ch }

    environment_ch.file_manifest_filename.map{ file(it.text) }
        .set{ file_manifest_ch }

    environment_ch.workflow.map{ it.text }
        .set{ workflow_ch }

    environment_ch.input_path.map{ it.text }
        .set{ input_path_ch }

    environment_ch.study_file.map{ file(it.text) }
        .set{ study_ch }

    environment_ch.diagnosis_file.map{ file(it.text) }
        .set{ diagnosis_ch }

    environment_ch.interventions_file.map{ file(it.text) }
        .set{ interventions_ch }

    environment_ch.channels_file.map{ file(it.text) }
        .set{ channels_file_ch }

    environment_ch.phenotypes_file.map{ file(it.text) }
        .set{ phenotypes_file_ch }

    environment_ch.db_config_file.map{ file(it.text) }
        .set{ db_config_file_ch }

    environment_ch.subjects_file.map{ file(it.text) }
        .set{ subjects_file_ch }

    environment_ch.outcomes_file.map{ file(it.text) }
        .set{ outcomes_file_ch }

    generate_run_information(
        workflow_ch,
        file_manifest_ch,
        input_path_ch,
        outcomes_file_ch,
    ).set { run_information_ch }

    run_information_ch
        .job_specification_table
        .splitCsv(header: true)
        .map{ row -> tuple(row.input_file_identifier, file(row.input_filename), row.job_index, row.outcome, row.sample_identifier) }
        .set{ job_specifications_ch }

    job_specifications_ch
        .map{ row -> row[1] }
        .collect()
        .set{ cell_manifest_files_ch }

    report_run_configuration(
        cell_manifest_files_ch,
        workflow_ch,
        file_manifest_ch,
        outcomes_file_ch,
        channels_ch,
        phenotypes_ch,
    )

    workflow_initialize(
        workflow_ch,
        file_manifest_ch,
        channels_ch,
        phenotypes_ch,
        outcomes_file_ch,
        db_config_file_ch,
        subjects_file_ch,
        cell_manifest_files_ch,
        study_ch,
        diagnosis_ch,
        interventions_ch,
    )
        .initialization_flag
        .set{ initialization_flag_ch }

    core_job(
        initialization_flag_ch,
        workflow_ch,
        job_specifications_ch,
        channels_ch,
        phenotypes_ch,
    )
        .set { core_job_results_ch }

    merge_databases(
        core_job_results_ch.metrics_database.collect(),
    )
        .metrics_database
        .set{ merged_metrics_database_ch }

    merge_performance_reports(
        core_job_results_ch.performance_report.collect()
    )

    aggregate_results(
        merged_metrics_database_ch,
        db_config_file_ch,
        file_manifest_ch,
        workflow_ch,
        channels_ch,
        phenotypes_ch,
    )
}
