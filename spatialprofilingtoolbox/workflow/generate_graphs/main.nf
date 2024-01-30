nextflow.enable.dsl = 2

include 'nf_files/graph_generation' as gg

workflow {
    gg.echo_environment_variables()
        .set{ environment_ch }
    
    environment_ch.db_config_file.map{ file(it.text) }
        .set{ db_config_file_ch }
    
    environment_ch.graph_config_file.map{ file(it.text) }
        .set{ graph_config_file_ch }
    
    gg.generate_graphs(
        db_config_file_ch,
        graph_config_file_ch
    ).set{ working_directory_ch }
}
