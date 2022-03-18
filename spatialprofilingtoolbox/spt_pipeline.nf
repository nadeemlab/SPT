
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
    manifest = parameters['file_manifest_file']
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

process single_job {
    input:
    path config_file
    path file_manifest_file
    tuple val(input_file_identifier), file(input_filename), val(job_index)
    path extra_dependencies

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
    publishDir 'results'

    input:
    path config_file
    path file_manifest_file
    path 'intermediate.0.db'
    path extra_dependencies

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

    single_job(
        config_file_ch,
        file_manifest_ch,
        jobs_ch,
        auxiliary_job_input_files_ch,
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
    )
}
