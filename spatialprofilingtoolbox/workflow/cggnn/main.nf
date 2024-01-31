nextflow.enable.dsl = 2

include { generate_graphs } from './nf_files/graph_generation'
include { train } from './nf_files/train'
include { upload_importance_scores } from './nf_files/upload_importance_scores'


process echo_environment_variables {
    output:
    path 'db_config_file',                  emit: db_config_file
    path 'graph_config_file',               emit: graph_config_file
    path 'cg_gnn_training_image',           emit: cg_gnn_training_image
    path 'cg_gnn_singularity_run_options',  emit: cg_gnn_singularity_run_options
    path 'upload_importances',              emit: upload_importances

    script:
    """
    #!/bin/bash
    echo -n "${db_config_file_}" > db_config_file
    echo -n "${graph_config_file_}" > graph_config_file
    echo -n "${cg_gnn_training_image_}" > cg_gnn_training_image
    echo -n "${cg_gnn_singularity_run_options_}" > cg_gnn_singularity_run_options
    echo -n "${upload_importances_}" > upload_importances
    """
}

workflow {
    echo_environment_variables()
        .set{ environment_ch }
    
    environment_ch.db_config_file.map{ file(it.text) }
        .set{ db_config_file_ch }
    
    environment_ch.graph_config_file.map{ file(it.text) }
        .set{ graph_config_file_ch }
    
    environment_ch.cg_gnn_training_image.map{ it.text }
        .set{ cg_gnn_training_image_ch }
    
    environment_ch.cg_gnn_singularity_run_options.map{ it.text }
        .set{ cg_gnn_singularity_run_options_ch }

    environment_ch.upload_importances.map{ it.text }
        .set{ upload_importances_ch }

    generate_graphs(
        db_config_file_ch,
        graph_config_file_ch,
    ).set{ working_directory_ch }

    train(
        cg_gnn_training_image_ch,
        cg_gnn_singularity_run_options_ch,
        working_directory_ch,
        graph_config_file_ch,
    ).set{ train_out }

    train_out.importances_csv_path
        .set{ importances_csv_path_ch }

    train_out.working_directory
        .set{ working_directory_ch }

    upload_importance_scores(
        upload_importances_ch,
        importances_csv_path_ch,
        db_config_file_ch,
        graph_config_file_ch,
    )
}
