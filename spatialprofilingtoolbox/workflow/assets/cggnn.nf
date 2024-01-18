
nextflow.enable.dsl = 2

process echo_environment_variables {
    output:
    path 'db_config_file',                  emit: db_config_file
    path 'graph_config_file',               emit: graph_config_file
    path 'cuda',                            emit: cuda
    path 'upload_importances',              emit: upload_importances

    script:
    """
    #!/bin/bash
    echo -n "${db_config_file_}" > db_config_file
    echo -n "${graph_config_file_}" > graph_config_file
    echo -n "${cuda_}" > cuda
    echo -n "${upload_importances_}" > upload_importances
    """
}

process prep_graph_creation {
    input:
    path db_config_file
    path graph_config_file

    output:
    path 'parameters.pkl',                      emit: parameter_file
    path 'specimens/*',                         emit: specimen_files


    script:
    """
    #!/bin/bash
    cp ${db_config_file} db_config_file
    spt graphs prepare-graph-creation \
        --config_path ${graph_config_file} \
        --output_directory .
    """
}

process create_specimen_graphs {
    input:
    path parameters_file
    path specimen_file

    output:
    path "${specimen_file.baseName}.pkl",   optional: true, emit: specimen_graph

    script:
    """
    #!/bin/bash

    spt graphs create-specimen-graphs \
        --specimen_hdf_path ${specimen_file} \
        --parameters_path ${parameters_file} \
        --output_directory .
    """
}

process finalize_graphs {
    publishDir '.', mode: 'copy'

    input:
    path parameters_file
    path graph_files

    output:
    path "results/",                     emit: working_directory

    script:
    """
    #!/bin/bash

    graph_files_array=(${graph_files})

    spt graphs finalize-graphs \
        --graph_files "\${graph_files_array[@]}" \
        --parameters_path ${parameters_file} \
        --output_directory results
    """
}

process train {
    publishDir '.', mode: 'copy'

    beforeScript 'export DOCKER_IMAGE="nadeemlab/spt-cg-gnn:\$(if [[ "${cuda}" == "True" ]]; then echo "cuda-"; fi)0.0.2"'

    container "\${DOCKER_IMAGE}"

    input:
    val cuda
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

process upload_importance_scores {
    input:
    val upload_importances
    path importances_csv_path
    path db_config_file
    path graph_config_file

    script:
    """
    #!/bin/bash

    if [[ "${upload_importances}" == "True" ]]
    then
        cp ${db_config_file} db_config_file
        spt graphs upload-importances \
            --importances_csv_path ${importances_csv_path} \
            --config_path ${graph_config_file}
    fi
    """
}

workflow {
    echo_environment_variables()
        .set{ environment_ch }
    
    environment_ch.db_config_file.map{ file(it.text) }
        .set{ db_config_file_ch }
    
    environment_ch.graph_config_file.map{ file(it.text) }
        .set{ graph_config_file_ch }
    
    environment_ch.cuda.map{ it.text }
        .set{ cuda_ch }

    environment_ch.upload_importances.map{ it.text }
        .set{ upload_importances_ch }

    prep_graph_creation(
        db_config_file_ch,
        graph_config_file_ch,
    ).set{ prep_out }

    prep_out.parameter_file
        .set{ parameters_ch }

    prep_out.specimen_files
        .flatten()
        .set{ specimens_ch }

    create_specimen_graphs(
        parameters_ch,
        specimens_ch
    ).set{ specimen_graphs_ch }

    specimen_graphs_ch
        .filter { it != null }
        .collect()
        .set{ all_specimen_graphs_ch }

    finalize_graphs(
        parameters_ch,
        all_specimen_graphs_ch
    ).set{ finalize_out }

    finalize_out.working_directory
        .set{ working_directory_ch }

    train(
        cuda_ch,
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
