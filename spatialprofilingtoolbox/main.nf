
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

process generate_job_specifications {
    input:
    val workflow
    path file_manifest_file
    val input_path

    output:
    path 'job_specification_table.csv', emit: job_specification_table
    path 'dataset_metadata_files_list.txt', emit: dataset_metadata_files_list

    script:
    """
    spt-generate-job-specifications \
     --workflow='$workflow' \
     --file-manifest-file='$file_manifest_file' \
     --input-path='$input_path' \
     --job-specification-table=job_specification_table.csv \
     --dataset-metadata-files-list-file=dataset_metadata_files_list.txt
    """
}

process extract_compartments {
    input:
    path cell_manifest_files

    output:
    path 'compartments.txt'

    script:
    """
    spt-extract-compartments $cell_manifest_files --compartments-list-file=compartments.txt
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

process semantic_parsing {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 5

    publishDir 'results'

    input:
    path file_manifest_file
    path extra_dependencies
    path compartments

    output:
    path 'normalized_source_data.db'

    script:
    """
    spt-pipeline semantic-parse
    """
}

process single_job {
    memory { 2.GB * task.attempt }

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 4

    input:
    path file_manifest_file
    tuple val(input_file_identifier), file(input_filename), val(job_index)
    path extra_dependencies
    path compartments

    output:
    path "intermediate${job_index}.db", emit: sqldb
    path "intermediate${job_index}.csv", emit: performancereport

    script:
    """
    spt-pipeline single-job --input-file-identifier="$input_file_identifier" --intermediate-database-filename=intermediate${job_index}.db
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
    path file_manifest_file
    path 'intermediate.0.db'
    path 'performance_report.0.md'
    path extra_dependencies
    path compartments

    output:
    file 'intermediate.db'
    file 'stats_tests.csv'
    file 'performance_report.md'

    script:
    """
    cp intermediate.0.db intermediate.db
    cp performance_report.0.md performance_report.md
    spt-pipeline aggregate-results --intermediate-database-filename=intermediate.db > stats_tests.csv
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

    generate_job_specifications(
        workflow_ch,
        file_manifest_ch,
        input_path_ch,
    ).set { specifications_ch }

    specifications_ch
        .job_specification_table
        .splitCsv(header: true)
        .map{ row -> tuple(row.input_file_identifier, file(row.input_filename), row.job_index) }
        .set{ job_specifications_ch }

    job_specifications_ch
        .map{ row -> row[1] }
        .set{ cell_manifest_files_ch }

    specifications_ch
        .dataset_metadata_files_list
        .map{ file(it) }
        .splitText(by: 1)
        .map{ file(it.trim()) }
        .collect()
        .set{ dataset_metadata_files_ch }

    job_specifications_ch
        .map{ row -> "intermediate" + row[2] + ".db" }
        .collect()
        .map{ names -> names.join(" ") }
        .set{ all_intermediate_database_filenames }

    report_version().set{ version_print }

    extract_compartments(
        cell_manifest_files_ch,
    )
        .set{ compartments_ch }

    single_job(
        file_manifest_ch,
        job_specifications_ch,
        dataset_metadata_files_ch,
        compartments_ch,
    )
        .set { single_job_results_ch }

    single_job_results_ch
        .sqldb
        .collect()
        .set{ all_intermediate_databases }

    single_job_results_ch
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
        file_manifest_ch,
        merged_database_ch,
        performance_report_ch,
        dataset_metadata_files_ch,
        compartments_ch,
    )
}
