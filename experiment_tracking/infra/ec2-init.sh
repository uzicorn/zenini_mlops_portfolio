#!/bin/bash

# The idea : Send secrets from ./.env to EC2 without passing through AWS secrets or SSM param store

# Purpose  : This script is part of a secret management workflow

# Graphic workflow :
# "script without secrets" --> ./.env --> "script with secrets" --> $INFRA_BUCKET --> Script executes on EC2
                                                                                     

# Steps :
# 1- Substitute the variable in this file with the ./.env values using the bash command envsubst,
#       then send the populated script to S3//:$INFRA_BUCKET ------------------> (see make upload_init_script_to_s3). 
# 2- EC2 instance has been given permission to retrieve the script ------------> (see infra/template.yml line 53).
# 3- It then retrieves it from S3 and execute it as part of its UserData ------> (see infra/template.yml line 70).
 
# Why not use AWS secrets or SSM param store ? 
# To measure the pain of a manual implementation.                           

set -e
# Update system
sudo yum update -y

# Install Python3.8
sudo amazon-linux-extras install python3.8 -y
pip3.8 install --upgrade pip

# Install MLflow and dependencies
pip3.8 install boto3 psycopg2-binary
pip3.8 install mlflow==$MLFLOW_VERSION

# Install Postgres
amazon-linux-extras enable postgresql14
yum clean metadata
yum install postgresql -y

# Run mlflow
python3.8 -m mlflow server \
    --backend-store-uri postgresql+psycopg2://$user:$password@$host:$port/$dbname \
    --default-artifact-root s3://$ARTIFACTS_BUCKET/ \
    --host 0.0.0.0 \
    --port 5000