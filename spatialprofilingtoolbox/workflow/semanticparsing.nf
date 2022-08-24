

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
