#!/bin/bash
source scripts/printing.sh

print_regular_line "1. Configuring the SAML2AWS profile."
saml2aws configure --region=us-east-1 --profile=spt-prod-aws-profile --url=https://ssofed.mskcc.org --idp-provider=Ping --idp-account=prod --username=SVC_SPT
# Then user provides enter commands and password.

echo ''
print_regular_line "2. Logging in to the SAML2AWS profile."
saml2aws login -a "prod"
# Then user provides enter commands and password, again.

echo ''
print_regular_line "3. Exporting login information to environment variables."
saml2aws script -a "prod" > _saml2aws_script.sh
source _saml2aws_script.sh

echo ''
print_regular_line "4. Checking that AWS tools tolerate this environment."
aws sts get-caller-identity
if [[ "$?" != "0" ]];
then
    echo "Something wrong with login environment variables."
    exit 1
fi

echo ''
print_regular_line "5. Updating Kubernetes configuration settings in local storage."
aws eks update-kubeconfig --region us-east-1 --name spt-prod
if [[ "$?" != "0" ]];
then
    echo "Something wrong with Kubernetes update of configuration."
    exit 1
fi
kubectl get pods
if [[ "$?" != "0" ]];
then
    echo "Unable to list pods."
    exit 1
fi
