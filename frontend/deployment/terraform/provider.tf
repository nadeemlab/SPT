terraform {
  backend "s3" {
    #TODO add account_owner - check the document from engineering
    bucket = "spt-prod-terra-state-bucket" # Replace with your bucket name
    key    = "terraform.tfstate"
    region = "us-east-1"
    #dynamodb_table = "spt-cluster-state-lock" # Replace with your DynamoDB table name
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.54.0"
    }
  }
  required_version = ">=1.3.8"
}

provider "aws" {
  region = var.region
}
