
nextflow.enable.dsl = 2

process echo_environment_variables {
    output:
    path 'workflow', emit: workflow
    path 'file_manifest_filename', emit: file_manifest_filename
    path 'input_path', emit: input_path

    script:
    """
    #!/bin/bash
    echo -n "$workflow_" > workflow
    echo -n "$file_manifest_filename_" > file_manifest_filename
    echo -n "$input_path_" > input_path
    """
}

process query_for_outcomes_file {
    input:
    path file_manifest_file
    val input_path

    output:
    path 'outcomes_filename', emit: outcomes_file
    path 'found', emit: found

    script:
    """
    spt-query-for-file-by-data-type \
     --data-type='Outcome' \
     --input-path='$input_path' \
     --file-manifest-file='$file_manifest_file' \
     --retrieved-filename-file=outcomes_filename \
     --found-status-file=found
    if [[ "\$(cat found)" == "0" ]];
    then
        echo -n "$input_path/$file_manifest_file" > outcomes_filename
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
    path 'job_specification_table.csv', emit: job_specification_table
    path 'dataset_metadata_files_list.txt', emit: dataset_metadata_files_list
    path 'elementary_phenotypes_filename', emit: elementary_phenotypes_filename
    path 'composite_phenotypes_filename', emit: composite_phenotypes_filename

    script:
    """
    spt-generate-run-information \
     --workflow='$workflow' \
     --file-manifest-file='$file_manifest_file' \
     --input-path='$input_path' \
     --outcomes-file='$outcomes_file' \
     --job-specification-table=job_specification_table.csv \
     --dataset-metadata-files-list-file=dataset_metadata_files_list.txt \
     --elementary-phenotypes-filename=elementary_phenotypes_filename \
     --composite-phenotypes-filename=composite_phenotypes_filename
    """
}

process query_for_compartments_file {
    input:
    path file_manifest_file
    val input_path

    output:
    path 'compartments_filename', emit: compartments_file
    path 'found', emit: found

    script:
    """
    spt-query-for-file-by-identifier \
     --file-identifier='Compartments file' \
     --input-path='$input_path' \
     --file-manifest-file='$file_manifest_file' \
     --retrieved-filename-file=compartments_filename \
     --found-status-file=found
    if [[ "\$(cat found)" == "0" ]];
    then
        echo -n "$input_path/$file_manifest_file" > compartments_filename
    fi
    """
}

process extract_compartments {
    input:
    path compartments_file_if_known
    path found
    path cell_manifest_files

    output:
    path '.compartments.txt', emit: compartments_file

    script:
    """
    if [[ "\$(cat $found)" == "1" ]];
    then
        cp $compartments_file_if_known .compartments.txt
    else
        spt-extract-compartments \
         $cell_manifest_files \
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
    path file_manifest_file
    tuple val(input_file_identifier), file(input_filename), val(job_index), val(outcome), val(sample_identifier)
    path elementary_phenotypes
    path composite_phenotypes
    path compartments

    output:
    path "intermediate${job_index}.db", emit: sqldb
    path "intermediate${job_index}.csv", emit: performancereport

    script:
    """
    spt-core-job \
     --workflow='$workflow' \
     --input-file-identifier='$input_file_identifier' \
     --input-filename='$input_filename' \
     --sample-identifier='$sample_identifier' \
     --outcome='$outcome' \
     --elementary-phenotypes-file='$elementary_phenotypes' \
     --composite-phenotypes-file='$composite_phenotypes' \
     --compartments-file='$compartments' \
     --intermediate-database-filename=intermediate${job_index}.db
    """
}

process report_version {
    output:
    stdout

    script:
    """
    #!/bin/bash
    echo -n "SPT v"
    spt-print version
    """
}

process merge_databases {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 6

    input:
    path all_databases
    val all_database_filenames
    path all_performance_reports

    output:
    path 'merged.db', emit: sqldb
    path 'performance_report.md', emit: performancereport

    script:
    """
    spt-merge-sqlite-dbs $all_database_filenames --output=merged.db
    """
}

process aggregate_results {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 6

    publishDir 'results'

    input:
    path 'intermediate.0.db'
    path 'performance_report.0.md'
    val workflow
    path elementary_phenotypes
    path composite_phenotypes
    path compartments
    path outcomes_file

    output:
    file 'intermediate.db'
    file 'stats_tests.csv'
    file 'performance_report.md'

    script:
    """
    cp intermediate.0.db intermediate.db
    cp performance_report.0.md performance_report.md
    spt-aggregate-core-results \
     --workflow='$workflow' \
     --intermediate-database-filename=intermediate.db \
     --elementary-phenotypes-file='$elementary_phenotypes' \
     --composite-phenotypes-file='$composite_phenotypes' \
     --compartments-file='$compartments' \
     --outcomes-file='$outcomes_file' \
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
        .dataset_metadata_files_list
        .map{ file(it) }
        .splitText(by: 1)
        .map{ file(it.trim()) }
        .collect()
        .set{ dataset_metadata_files_ch }

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


    core_job(
        workflow_ch,
        file_manifest_ch,
        job_specifications_ch,
        elementary_phenotypes_ch,
        composite_phenotypes_ch,
        compartments_ch,
    )
        .set { core_job_results_ch }


    job_specifications_ch
        .map{ row -> "intermediate" + row[2] + ".db" }
        .collect()
        .map{ names -> names.join(" ") }
        .set{ all_intermediate_database_filenames }

    report_version().set{ version_print }

    core_job_results_ch
        .sqldb
        .collect()
        .set{ all_intermediate_databases }

    core_job_results_ch
        .performancereport
        .collect()
        .set{ all_performance_reports_ch }

    merge_databases(
        all_intermediate_databases,
        all_intermediate_database_filenames,
        all_performance_reports_ch,
    ).set{ merged_db_ch }

    merged_db_ch
        .sqldb
        .collect()
        .set{ merged_database_ch }

    merged_db_ch
        .performancereport
        .collect()
        .set{ performance_report_ch }

    aggregate_results(
        merged_database_ch,
        performance_report_ch,
        workflow_ch,
        elementary_phenotypes_ch,
        composite_phenotypes_ch,
        compartments_ch,
        outcomes_file_ch,
    )
}
