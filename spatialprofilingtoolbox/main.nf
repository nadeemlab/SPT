
nextflow.enable.dsl = 2

process echo_environment_variables {
    output:
    path 'workflow',                        emit: workflow
    path 'file_manifest_filename',          emit: file_manifest_filename
    path 'input_path',                      emit: input_path

    script:
    """
    #!/bin/bash
    echo -n "${workflow_}" > workflow
    echo -n "${file_manifest_filename_}" > file_manifest_filename
    echo -n "${input_path_}" > input_path
    """
}

process query_for_outcomes_file {
    input:
    path file_manifest_file
    val input_path

    output:
    path 'outcomes_filename',               emit: outcomes_file
    path 'found',                           emit: found

    script:
    """
    spt-query-for-file \
     --data-type='Outcome' \
     --input-path='${input_path}' \
     --file-manifest-file='${file_manifest_file}' \
     --retrieved-filename-file=outcomes_filename > found
    if [[ "\$(cat found)" == "0" ]];
    then
        echo -n "${input_path}/${file_manifest_file}" > outcomes_filename
    fi
    """
}

process query_for_compartments_file {
    input:
    path file_manifest_file
    val input_path

    output:
    path 'compartments_filename',           emit: compartments_file
    path 'found',                           emit: found

    script:
    """
    spt-query-for-file \
     --file-identifier='Compartments file' \
     --input-path='${input_path}' \
     --file-manifest-file='${file_manifest_file}' \
     --retrieved-filename-file=compartments_filename > found
    if [[ "\$(cat found)" == "0" ]];
    then
        echo -n "${input_path}/${file_manifest_file}" > compartments_filename
    fi
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
    path 'elementary_phenotypes_filename',  emit: elementary_phenotypes_filename
    path 'composite_phenotypes_filename',   emit: composite_phenotypes_filename

    script:
    """
    spt-generate-run-information \
     --workflow='${workflow}' \
     --file-manifest-file='${file_manifest_file}' \
     --input-path='${input_path}' \
     --outcomes-file='${outcomes_file}' \
     --job-specification-table=job_specification_table.csv \
     --elementary-phenotypes-filename=elementary_phenotypes_filename \
     --composite-phenotypes-filename=composite_phenotypes_filename
    """
}

process extract_compartments {
    input:
    path compartments_file_if_known
    path found
    path cell_manifest_files

    output:
    path '.compartments.txt',               emit: compartments_file

    script:
    """
    if [[ "\$(cat ${found})" == "1" ]];
    then
        cp ${compartments_file_if_known} .compartments.txt
    else
        spt-extract-compartments \
         ${cell_manifest_files} \
         --compartments-list-file=.compartments.txt
    fi
    """
}

process core_job {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 4

    input:
    val workflow
    tuple val(input_file_identifier), file(input_filename), val(job_index), val(outcome), val(sample_identifier)
    path elementary_phenotypes
    path composite_phenotypes
    path compartments

    output:
    path "metrics${job_index}.db",          emit: metrics_database
    path "metrics${job_index}.csv",         emit: performance_report

    script:
    """
    spt-core-job \
     --workflow='${workflow}' \
     --input-file-identifier='${input_file_identifier}' \
     --input-filename='${input_filename}' \
     --sample-identifier='${sample_identifier}' \
     --outcome='${outcome}' \
     --elementary-phenotypes-file='${elementary_phenotypes}' \
     --composite-phenotypes-file='${composite_phenotypes}' \
     --compartments-file='${compartments}' \
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
    path elementary_phenotypes
    path composite_phenotypes
    path compartments

    output:
    path "run_configuration.log"

    script:
    """
    spt-report-run-configuration \
     --workflow='${workflow}' \
     --file-manifest-file='${file_manifest_file}' \
     --outcomes-file='${outcomes_file}' \
     --elementary-phenotypes-file='${elementary_phenotypes}' \
     --composite-phenotypes-file='${composite_phenotypes}' \
     --compartments-file='${compartments}' >& run_configuration.log
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
    spt-merge-sqlite-dbs ${all_metrics_databases} --output=metrics_database.db
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
    spt-merge-performance-reports ${all_performance_reports} --output=performance_report.md
    """
}

process aggregate_results {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 6

    publishDir 'results'

    input:
    path metrics_database
    val workflow
    path elementary_phenotypes
    path composite_phenotypes
    path compartments
    path outcomes_file

    output:
    file 'stats_tests.csv'

    script:
    """
    spt-aggregate-core-results \
     --workflow='${workflow}' \
     --metrics-database-filename=${metrics_database} \
     --elementary-phenotypes-file='${elementary_phenotypes}' \
     --composite-phenotypes-file='${composite_phenotypes}' \
     --compartments-file='${compartments}' \
     --outcomes-file='${outcomes_file}' \
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

    query_for_outcomes_file(
        file_manifest_ch,
        input_path_ch,
    )
        .outcomes_file
        .map{ file(it.text) }
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

    run_information_ch
        .elementary_phenotypes_filename
        .map{ file(it.text) }
        .set{ elementary_phenotypes_ch }

    run_information_ch
        .composite_phenotypes_filename
        .map{ file(it.text) }
        .set{ composite_phenotypes_ch }

    job_specifications_ch
        .map{ row -> row[1] }
        .collect()
        .set{ cell_manifest_files_ch }

    query_for_compartments_file(
        file_manifest_ch,
        input_path_ch,
    ).set{ compartments_query_ch }

    extract_compartments(
        compartments_query_ch.compartments_file.map{ file(it.text) },
        compartments_query_ch.found,
        cell_manifest_files_ch,
    )
        .compartments_file
        .set{ compartments_ch }

    report_run_configuration(
        cell_manifest_files_ch,
        workflow_ch,
        file_manifest_ch,
        outcomes_file_ch,
        elementary_phenotypes_ch,
        composite_phenotypes_ch,
        compartments_ch,
    )

    core_job(
        workflow_ch,
        job_specifications_ch,
        elementary_phenotypes_ch,
        composite_phenotypes_ch,
        compartments_ch,
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
        workflow_ch,
        elementary_phenotypes_ch,
        composite_phenotypes_ch,
        compartments_ch,
        outcomes_file_ch,
    )
}
