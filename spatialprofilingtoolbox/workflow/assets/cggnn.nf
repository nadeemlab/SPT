
nextflow.enable.dsl = 2

process echo_environment_variables {
    output:
    path 'db_config_file',                  emit: db_config_file
    path 'study_name',                      emit: study_name
    path 'strata',                          emit: strata
    path 'validation_data_percent',         emit: validation_data_percent
    path 'test_data_percent',               emit: test_data_percent
    path 'disable_channels',                emit: disable_channels
    path 'disable_phenotypes',              emit: disable_phenotypes
    path 'cells_per_slide_target',          emit: cells_per_slide_target
    path 'target_name',                     emit: target_name
    path 'in_ram',                          emit: in_ram
    path 'batch_size',                      emit: batch_size
    path 'epochs',                          emit: epochs
    path 'learning_rate',                   emit: learning_rate
    path 'k_folds',                         emit: k_folds
    path 'explainer_model',                 emit: explainer_model
    path 'merge_rois',                      emit: merge_rois
    path 'upload_importances',              emit: upload_importances
    path 'random_seed',                     emit: random_seed

    script:
    """
    #!/bin/bash
    echo -n "${db_config_file_}" > db_config_file
    echo -n "${study_name_}" > study_name
    echo -n "${strata_}" > strata
    echo -n "${validation_data_percent_}" > validation_data_percent
    echo -n "${test_data_percent_}" > test_data_percent
    echo -n "${disable_channels_}" > disable_channels
    echo -n "${disable_phenotypes_}" > disable_phenotypes
    echo -n "${cells_per_slide_target_}" > cells_per_slide_target
    echo -n "${target_name_}" > target_name
    echo -n "${in_ram_}" > in_ram
    echo -n "${batch_size_}" > batch_size
    echo -n "${epochs_}" > epochs
    echo -n "${learning_rate_}" > learning_rate
    echo -n "${k_folds_}" > k_folds
    echo -n "${explainer_model_}" > explainer_model
    echo -n "${merge_rois_}" > merge_rois
    echo -n "${upload_importances_}" > upload_importances
    echo -n "${random_seed_}" > random_seed
    """
}

process prep_graph_creation {
    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 4

    input:
    path db_config_file
    val study_name
    val strata
    val validation_data_percent
    val test_data_percent
    val disable_channels
    val disable_phenotypes
    val cells_per_slide_target
    val target_name

    output:
    path 'parameters.pkl',                      emit: parameter_file
    path 'specimens/*',                         emit: specimen_files


    script:
    """
    #!/bin/bash

    strata_option=\$( if [[ "${strata}" != "all" ]]; then echo "--strata ${strata}"; fi)
    disable_channels_option=\$( if [[ "${disable_channels}" == "true" ]]; then echo "--disable_channels"; fi)
    disable_phenotypes_option=\$( if [[ "${disable_phenotypes}" = "true" ]]; then echo "--disable_phenotypes"; fi)

    echo \
     --database-config-file \\'${db_config_file}\\' \
     --study-name \\'${study_name}\\' \
     \${strata_option} \
     --validation_data_percent ${validation_data_percent} \
     --test_data_percent ${test_data_percent} \
     \${disable_channels_option} \
     \${disable_phenotypes_option} \
     --cells_per_slide_target ${cells_per_slide_target} \
     --target_name \\'${target_name}\\' \
     --output_directory . \
     | xargs spt cggnn prepare-graph-creation
    """
}

process create_specimen_graphs {
    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 4

    input:
    path parameters_file
    path specimen_file

    output:
    path "${specimen_file.baseName}.bin",    emit: specimen_graph

    script:
    """
    #!/bin/bash

    spt cggnn create-specimen-graphs \
        --specimen_hdf_path ${specimen_file} \
        --parameters_path ${parameters_file} \
        --output_directory .
    """
}

process finalize_graphs {
    publishDir '.', mode: 'copy'

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 4

    input:
    path parameters_file
    path graph_files

    output:
    path "results/",                     emit: working_directory
    path "results/feature_names.txt",    emit: feature_names_file
    path "results/graphs.bin",           emit: graphs_file
    path "results/graph_info.pkl",       emit: graph_metadata_file

    script:
    """
    #!/bin/bash

    graph_files_array=(${graph_files})

    spt cggnn finalize-graphs \
        --graph_files "\${graph_files_array[@]}" \
        --parameters_path ${parameters_file} \
        --output_directory results
    """
}

process train {
    publishDir '.', mode: 'copy'

    errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
    maxRetries 4

    input:
    path working_directory
    val in_ram
    val batch_size
    val epochs
    val learning_rate
    val k_folds
    val explainer_model
    val merge_rois
    val random_seed

    output:
    path "${working_directory}/importances.csv",     emit: importances_csv_path
    path "${working_directory}/model/",              emit: model_directory
    path "${working_directory}/graphs.bin",          optional: true

    script:
    """
    #!/bin/bash

    in_ram_option=\$( if [[ "${in_ram}" == "true" ]]; then echo "--in_ram"; fi)
    explainer_option=\$( if [[ "${explainer_model}" != "none" ]]; then echo "--explainer ${explainer_model}"; fi)
    merge_rois_option=\$( if [[ "${merge_rois}" == "true" ]]; then echo "--merge_rois"; fi)

    echo \
     --cg_directory ${working_directory} \
     \${in_ram_option} \
     --batch_size ${batch_size} \
     --epochs ${epochs} \
     --learning_rate \\'${learning_rate}\\' \
     --k_folds ${k_folds} \
     \${explainer_option} \
     \${merge_rois_option} \
     | xargs spt cggnn train
    """
}

process upload_importance_scores {
    input:
    val upload_importances
    path importances_csv_path

    script:
    """
    #!/bin/bash

    if [[ "${upload_importances}" == "true" ]]
    then
        spt cggnn upload-importances \
            --importances_csv_path ${importances_csv_path}
    fi
    """
}

workflow {
    echo_environment_variables()
        .set{ environment_ch }

    environment_ch.db_config_file.map{ file(it.text) }
        .set{ db_config_file_ch }

    environment_ch.study_name.map{ it.text }
        .set{ study_name_ch }

    environment_ch.strata.map{ it.text }
        .set{ strata_ch }

    environment_ch.validation_data_percent.map{ it.text }
        .set{ validation_data_percent_ch }

    environment_ch.test_data_percent.map{ it.text }
        .set{ test_data_percent_ch }

    environment_ch.disable_channels.map{ it.text }
        .set{ disable_channels_ch }

    environment_ch.disable_phenotypes.map{ it.text }
        .set{ disable_phenotypes_ch }

    environment_ch.cells_per_slide_target.map{ it.text }
        .set{ cells_per_slide_target_ch }

    environment_ch.target_name.map{ it.text }
        .set{ target_name_ch }

    environment_ch.in_ram.map{ it.text }
        .set{ in_ram_ch }

    environment_ch.batch_size.map{ it.text }
        .set{ batch_size_ch }

    environment_ch.epochs.map{ it.text }
        .set{ epochs_ch }

    environment_ch.learning_rate.map{ it.text }
        .set{ learning_rate_ch }

    environment_ch.k_folds.map{ it.text }
        .set{ k_folds_ch }

    environment_ch.explainer_model.map{ it.text }
        .set{ explainer_model_ch }

    environment_ch.merge_rois.map{ it.text }
        .set{ merge_rois_ch }

    environment_ch.upload_importances.map{ it.text }
        .set{ upload_importances_ch }

    environment_ch.random_seed.map{ it.text }
        .set{ random_seed_ch }

    prep_graph_creation(
        db_config_file_ch,
        study_name_ch,
        strata_ch,
        validation_data_percent_ch,
        test_data_percent_ch,
        disable_channels_ch,
        disable_phenotypes_ch,
        cells_per_slide_target_ch,
        target_name_ch
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
        .collect()
        .set{ all_specimen_graphs_ch }

    finalize_graphs(
        parameters_ch,
        all_specimen_graphs_ch
    ).set{ finalize_out }

    finalize_out.working_directory
        .set{ working_directory_ch }

    finalize_out.feature_names_file
        .set{ feature_names_ch }

    finalize_out.graphs_file
        .set{ graphs_file_ch }

    finalize_out.graph_metadata_file
        .set{ graph_metadata_ch }

    train(
        working_directory_ch,
        in_ram_ch,
        batch_size_ch,
        epochs_ch,
        learning_rate_ch,
        k_folds_ch,
        explainer_model_ch,
        merge_rois_ch,
        random_seed_ch
    ).set{ train_out }

    train_out.importances_csv_path
        .set{ importances_csv_path_ch }

    train_out.model_directory
        .set{ model_directory_ch }

    upload_importance_scores(
        upload_importances_ch,
        importances_csv_path_ch
    )
}
