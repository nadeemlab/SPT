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
        cp ${db_config_file} spt_db.config
        spt graphs upload-importances \
            --importances_csv_path ${importances_csv_path} \
            --config_path ${graph_config_file}
    fi
    """
}
