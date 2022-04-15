
nextflow.enable.dsl = 2

process retrieve_file_manifest_file {
    input:
    path config_file

    output:
    stdout

    script:
    """
    #!/usr/bin/env python3
    import os
    from os.path import join
    import json

    parameters = json.load(open('$config_file', 'rt'))
    input_path = parameters['input_path']
    if 'file_manifest_file' in parameters:
        manifest = parameters['file_manifest_file']
    else:
        manifest = 'file_manifest.tsv'
    file_manifest_file = join(input_path, manifest)
    print(file_manifest_file, end='')
    """
}

process list_auxiliary_job_inputs {
    input:
    path config_file
    path file_manifest_file

    output:
    path 'job_input_files.txt'

    script:
    """
    spt-pipeline list-auxiliary-job-inputs --job-inputs=job_input_files.txt
    """
}

process generate_jobs {
    input:
    path config_file
    path file_manifest_file

    output:
    stdout

    script:
    """
    spt-pipeline generate-jobs
    """
}

process list_all_jobs_inputs {
    input:
    path config_file
    path file_manifest_file

    output:
    path 'all_jobs_input_files.txt'

    script:
    """
    spt-pipeline list-all-jobs-inputs --all-jobs-inputs=all_jobs_input_files.txt
    """
}

process list_all_compartments {
    input:
    path config_file
    path file_manifest_file
    path extra_dependencies

    output:
    path 'compartments.txt'

    script:
    """
    spt-pipeline list-all-compartments --compartments-file=compartments.txt
    """
}

process semantic_parsing {
    publishDir 'results'

    input:
    path config_file
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
    path config_file
    path file_manifest_file
    tuple val(input_file_identifier), file(input_filename), val(job_index)
    path extra_dependencies
    path compartments

    output:
    file "intermediate${job_index}.db"

    script:
    """
    spt-pipeline single-job --input-file-identifier="$input_file_identifier" --intermediate-database-filename=intermediate${job_index}.db
    """
}

process merge_databases {
    input:
    path all_databases
    val all_database_filenames

    output:
    file 'merged.db'

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
    path config_file
    path file_manifest_file
    path 'intermediate.0.db'
    path extra_dependencies
    path compartments

    output:
    file 'intermediate.db'
    file 'stats_tests.csv'

    script:
    """
    cp intermediate.0.db intermediate.db
    spt-pipeline aggregate-results --intermediate-database-filename=intermediate.db > stats_tests.csv
        """
}

workflow {
    config_filename = ".spt_pipeline.json"
    channel.value(config_filename)
        .map{ file(it) }
        .set{ config_file_ch }

    retrieve_file_manifest_file(config_file_ch)
        .map{ file(it) }
        .set{ file_manifest_ch }

    generate_jobs(
        config_file_ch,
        file_manifest_ch,
    )
        .splitCsv(header: true)
        .map{ row -> tuple(row.input_file_identifier, file(row.input_filename), row.job_index) }
        .set{ jobs_ch }

    jobs_ch
        .map{ row -> "intermediate" + row[2] + ".db" }
        .collect()
        .map{ names -> names.join(" ") }
        .set{ all_intermediate_database_filenames }

    list_auxiliary_job_inputs(
        config_file_ch,
        file_manifest_ch,
    )
        .map{ file(it) }
        .splitText(by: 1)
        .map{ file(it.trim()) }
        .collect()
        .set{ auxiliary_job_input_files_ch }

    list_all_jobs_inputs(
        config_file_ch,
        file_manifest_ch,
    )
        .map{ file(it) }
        .splitText(by: 1)
        .map{ file(it.trim()) }
        .collect()
        .set{ all_job_input_files_ch }

    list_all_compartments(
        config_file_ch,
        file_manifest_ch,
        all_job_input_files_ch,
    )
        .map{ file(it) }
        .splitText(by: 1)
        .map{ file(it.trim()) }
        .collect()
        .set{ compartments_ch }

    semantic_parsing(
        config_file_ch,
        file_manifest_ch,
        all_job_input_files_ch,
        compartments_ch,
    )

    single_job(
        config_file_ch,
        file_manifest_ch,
        jobs_ch,
        auxiliary_job_input_files_ch,
        compartments_ch,
    )
        .collect()
        .set{ all_intermediate_databases }

    merge_databases(
        all_intermediate_databases,
        all_intermediate_database_filenames,
    )
        .set{ merged_database_ch }

    aggregate_results(
        config_file_ch,
        file_manifest_ch,
        merged_database_ch,
        auxiliary_job_input_files_ch,
        compartments_ch,
    )
}
