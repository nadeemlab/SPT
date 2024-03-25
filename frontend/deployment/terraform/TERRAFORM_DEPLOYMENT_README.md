

Before the deployment it is necessary to check with the Enigineering team on providing the TLS certificate
in the AWS for the application. It should be stored in the AWS resources [Certificate](https://us-east-1.console.aws.amazon.com/acm/home?region=us-east-1#/certificates/list)

Also it is improtant to remember, that **all team members** involved in deployment should try to deploy everything from **mskAutomationUser** role using credentials provided from engineering team. If you use different roles and accounts (mskOperator of mskEngineer) it might lead to conflicts and unexpected behavior of terraform and its malformed state.

# Terraform deployment #

[Terraform](https://developer.hashicorp.com/terraform/intro) is a tool for provisioning cloud computing infrastructure, organized around the idea of "applying" declarative configuration files.

- [Terraform deployment](#terraform-deployment)
  - [Configure the local environment for aws operations](#configure-the-local-environment-for-aws-operations)
  - [Create S3 bucket to store **Terraform** state](#create-s3-bucket-to-store-terraform-state)
  - [Terraform commands](#terraform-commands)
    - [Installation](#installation)
    - [Initialization](#initialization)
    - [Create new workspace](#create-new-workspace)
    - [Update packages](#update-packages)
    - [Plan the configuration changes](#plan-the-configuration-changes)
    - [Apply the planned changes to the infrastructure using .tfvars file](#apply-the-planned-changes-to-the-infrastructure-using-tfvars-file)
    - [Collect the required output values for future usage with helm charts](#collect-the-required-output-values-for-future-usage-with-helm-charts)


## Configure the local environment for aws operations ##

0. Install [saml2aws utility](https://github.com/Versent/saml2aws). It allows SSO login credentials to be used to manage AWS through the AWS CLI. On Linux this may require the brew package manager, even though there is a direct-download Linux distribution provided.
1. **saml2aws configure** to enter the credentials and login details:
```sh
saml2aws configure --region=us-east-1 --profile=spt-prod-final --url=https://ssofed.mskcc.org --idp-provider=Ping --username=<username>
```
2. **saml2aws login** to actually authorise via SSO login. You might need to be on the VPN for this step to work.
3. **saml2aws script** to recieve AWS access tokens as environment variable definitions. You might use `eval "$(saml2aws script)"` to put these variables into the current shell's environment.
4. **aws sts get-caller-identity** to check logged in role. Requires AWS CLI, which may be available with `apt install awscli`, but if this version doesn't work, the PyPI-provided Python package `awscli` may work instead.


## Create S3 bucket to store **Terraform** state 

Terraform can store its state in S3 AWS bucket, we need to create one and apply an appropriate security policy for it:
```sh
aws s3 mb s3://spt-terra-state-bucket --region us-east-1
```

1. After creation, you need to block public access to this S3 bucket (**manually**). Add the following policy to the S3 bucket manually through the S3 web interface (replace the placeholders accordingly):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:sts::666466118732:role/mskAutomationUser"
            },
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::spt-prod-terra-state-bucket"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:sts::666466118732:role/mskAutomationUser"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::spt-prod-terra-state-bucket/*"
        }
    ]
}
```

2. **aws s3api put-bucket-versioning --bucket spt-dev-terra-state-bucket --versioning-configuration Status=Enabled**. (*What does this line do? It enables "versioning"?*)

Now the state will be stored in the S3 bucket.

## Terraform commands ##
### Installation ###
0. First [install `terraform`](https://developer.hashicorp.com/terraform/downloads).

### Initialization ###
1. `cd terraform/`
2. `terraform init`. This step initializes the working directory. From the Terraform documentation:
```txt
... This sets up all the local data necessary to run Terraform that is typically not committed to version control. ...
... This command is always safe to run multiple times. ...
```

(For future: Create script `./set_bucket_name.sh` to replace `var.state_bucket` with correct value.)

### Create new workspace ###
3. **terraform workspace new prod**
4. **terraform workspace list**
5. **terraform workspace select prod**

### Update packages ###
6. **terraform get -update**
   
### Plan the configuration changes ###
7. **terraform plan -var-file=dev.tfvars**
   
Check the values in the **terraform plan** output

### Apply the planned changes to the infrastructure using .tfvars file ###
8.  **terraform apply -var-file=dev.tfvars**

### Collect the required output values for future usage with helm charts ###
(For this, you can use `./record_terraform_output.sh`.)
9.  **terraform output -raw values_rds > tf_rds_values.yaml**
10. **terraform output -raw values_elb > tf_values_elb.yaml**  
11. **terraform output -raw values_ingress > tf_values_ingress.yaml**
12. **terraform output -raw values_s3_mounter > tf_s3_mounter.yaml**
