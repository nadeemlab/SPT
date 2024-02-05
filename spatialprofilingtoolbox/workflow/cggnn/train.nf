process train {
    publishDir '.', mode: 'copy'

    container "${cg_gnn_training_image}"
    containerOptions "${cg_gnn_singularity_run_options}"

    input:
    val cg_gnn_training_image
    val cg_gnn_singularity_run_options
    path working_directory
    path graph_config_file

    output:
    path "${working_directory}/importances.csv",     emit: importances_csv_path
    path "${working_directory}/",                    emit: working_directory

    script:
    """
    #!/bin/bash

    spt-plugin-train-on-graphs \
        --input_directory ${working_directory} \
        --config_file ${graph_config_file} \
        --output_directory ${working_directory}
    """
}
