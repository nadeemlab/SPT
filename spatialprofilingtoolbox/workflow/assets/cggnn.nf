
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
    // path 'roi_side_length',                 emit: roi_side_length
    path 'cells_per_slide_target',          emit: cells_per_slide_target
    path 'target_name',                     emit: target_name
    path 'in_ram',                          emit: in_ram
    path 'batch_size',                      emit: batch_size
    path 'epochs',                          emit: epochs
    path 'learning_rate',                   emit: learning_rate
    path 'k_folds',                         emit: k_folds
    path 'explainer_model',                 emit: explainer_model
    path 'merge_rois',                      emit: merge_rois
    path 'prune_misclassified',             emit: prune_misclassified
    path 'output_prefix',                   emit: output_prefix
    path 'upload_importances',              emit: upload_importances

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
    echo -n "${prune_misclassified_}" > prune_misclassified
    echo -n "${output_prefix_}" > output_prefix
    echo -n "${upload_importances_}" > upload_importances
    """
}

process run_cggnn {
    publishDir 'results'

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
    // val roi_side_length
    val cells_per_slide_target
    val target_name
    val in_ram
    val batch_size
    val epochs
    val learning_rate
    val k_folds
    val explainer_model
    val merge_rois
    val prune_misclassified
    val output_prefix
    val upload_importances

    output:
    // path "${output_prefix}_cells.h5",                emit: cells
    // path "${output_prefix}_lables.h5",               emit: labels
    // path "${output_prefix}_label_to_result.json",    emit: label_to_result
    path "${output_prefix}_importances.csv"
    path "${output_prefix}_model.pt"


    shell:
    '''
    spt cggnn run \
        --spt_db_config_location "!{db_config_file}" \
        --study "!{study_name}" \
        $(if [[ "!{strata}" != all ]]; then echo "--strata !{strata}"; fi) \
        --validation_data_percent !{validation_data_percent} \
        --test_data_percent !{test_data_percent} \
        $(if [[ "!{disable_channels}" = true ]]; then echo "--disable_channels"; fi) \
        $(if [[ "!{disable_phenotypes}" = true ]]; then echo "--disable_phenotypes"; fi) \
        --cells_per_slide_target !{cells_per_slide_target} \
        $(if [[ "!{target_name}" != none ]]; then echo "--target_name "!{target_name}""; fi) \
        $(if [[ "!{in_ram}" = true ]]; then echo "--in_ram"; fi) \
        --batch_size !{batch_size} \
        --epochs !{epochs} \
        --learning_rate !{learning_rate} \
        --k_folds !{k_folds} \
        --explainer_model "!{explainer_model}" \
        $(if [[ "!{merge_rois}" = true ]]; then echo "--merge_rois"; fi) \
        $(if [[ "!{prune_misclassified}" = true ]]; then echo "--prune_misclassified"; fi) \
        --output_prefix "!{output_prefix}" \
        $(if [[ "!{upload_importances}" = true ]]; then echo "--upload_importances"; fi)
    '''
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
    
    // environment_ch.roi_side_length.map{ it.text }
    //     .set{ roi_side_length_ch }
    
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
    
    environment_ch.prune_misclassified.map{ it.text }
        .set{ prune_misclassified_ch }
    
    environment_ch.output_prefix.map{ it.text }
        .set{ output_prefix_ch }
    
    environment_ch.upload_importances.map{ it.text }
        .set{ upload_importances_ch }
    
    run_cggnn(
        db_config_file_ch,
        study_name_ch,
        strata_ch,
        validation_data_percent_ch,
        test_data_percent_ch,
        disable_channels_ch,
        disable_phenotypes_ch,
        // roi_side_length_ch,
        cells_per_slide_target_ch,
        target_name_ch,
        in_ram_ch,
        batch_size_ch,
        epochs_ch,
        learning_rate_ch,
        k_folds_ch,
        explainer_model_ch,
        merge_rois_ch,
        prune_misclassified_ch,
        output_prefix_ch,
        upload_importances_ch
    )
}
