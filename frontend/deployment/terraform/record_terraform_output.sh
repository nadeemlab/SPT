#!/bin/bash

terraform output -raw values_rds > tf_rds_values.yaml
terraform output -raw values_elb > tf_values_elb.yaml
terraform output -raw values_ingress > tf_values_ingress.yaml
terraform output -raw values_s3_mounter > tf_values_s3_mounter_prod.yaml
