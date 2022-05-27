Build the Docker container image for the API server.

```
docker build -t pathstatsapiappimage .
```

You can run the API server locally or on AWS.

### Locally
Make sure `.spt_db.config.env` contains `DB_ENDPOINT`, `DB_USER`, and `DB_PASSWORD`.

```
docker run -d --name pathstatsapiapp --env-file .spt_db.config.env -p 80:80 pathstatsapiappimage
```

To repeat the whole process for a rebuild and rerun:
```
docker build -t pathstatsapiappimage .
docker container stop pathstatsapiapp
docker container rm pathstatsapiapp
docker run -d --name pathstatsapiapp --env-file .spt_db.config.env -p 80:80 pathstatsapiappimage
```

### AWS
Create the task definition file.

Make sure `.aws_specific.config` contains section `[aws-database-info]` with variables `db_endpoint` and `db_password_arn`.
```
spt-generate-aws-task-definition \
 --task-definition-template=task_definition_pathstats_api_app.json.jinja \
 --configuration=.aws_specific.config
```

Use the generated `task_definition_pathstats_api_app.json`.
