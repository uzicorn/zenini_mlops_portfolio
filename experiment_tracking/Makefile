#!make
# Each recipe ruins in a unique schell
.ONESHELL:
#------------
# variables |
#------------
WORKDIR = /home/uzicorn/code/mlops/experiment_tracking
ENVPATH = $$(pwd)/.env

#------------
# SAM BUILD |
#------------
build_sam:
	cd infra/
	pwd 
	sam build \
		--template-file template.yaml \
		--config-file   config.toml

deploy_sam:
	. $(ENVPATH) 
	sam deploy \
		--no-confirm-changeset \
		--no-disable-rollback \
		--capabilities CAPABILITY_NAMED_IAM \
		--template-file $(WORKDIR)/infra/.aws-sam/build/template.yaml \
		--config-file   $(WORKDIR)/infra/config.toml \
		--parameter-overrides SubnetId=$${SUBNET_ID} SecurityGroupIds=$${EC2_SECURITY_GROUP} KeyName=$${KEYNAME} InfraBucket=$${INFRA_BUCKET} ArtifactsBucket=$${ARTIFACTS_BUCKET}

#---------------------
# EC2 initialization |
#---------------------
# A bash script stored in S3 is used to init the EC2 ressource
# It contains secret variables that has to be resolved before loading it to S3
# The variable are resolved in a temp file sent to S3 then removed
# Each deployement, the old script version is replaced
upload_init_script_to_s3:
	set -a
	. $(ENVPATH)
	envsubst < infra/ec2-init.sh > temp.sh
	awsv2 s3 cp temp.sh s3://mlops-serverless/ec2-init.sh
	rm temp.sh

#---------------
# Architecture |
#---------------
deploy_infra:
	set -e
	$(MAKE) upload_init_script_to_s3
	$(MAKE) build_sam
	$(MAKE) deploy_sam

#---------
# WebApp |
#---------
run_webapp:
	. $(ENVPATH)
	@cd ..
	$$PYTHON_INTERPRETER_PATH -m fastapi dev --port $$WEBAPP_PORT experiment_tracking/webapp/app.py
	@cd -
	$(MAKE) clear_pycache

#-----
# ML |
#-----
connect_ec2:
	. $(ENVPATH)
	echo $$EC2_PUBLIC_URL
	ssh -i secret/$$KEYNAME.pem ec2-user@$$EC2_PUBLIC_URL

ingest:
	. $(ENVPATH)
	cd ..
	$$PYTHON_INTERPRETER_PATH -m experiment_tracking.ingestion.ingest
	cd -
	$(MAKE) clear_pycache

train_iris_classification:
	. $(ENVPATH)
	@cd ..
	$$PYTHON_INTERPRETER_PATH -m experiment_tracking.training.train_iris_classification
	@cd -
	$(MAKE) clear_pycache

#----------
# Cleanup |
#----------

# For dev purposes, delete all rows in backend tables 
delete_mlflow_backend:
	@echo "Deleting all rows in MlFlow's RDS backend (except alembic schema version!)"
	set -a; . $(ENVPATH) 
	psql "postgres://$$user:$$password@$$host:$$port/$$dbname" \
		-c "TRUNCATE TABLE \
			public.datasets, \
			public.experiment_tags, \
			public.experiments, \
			public.input_tags, \
			public.inputs, \
			public.latest_metrics, \
			public.metrics, \
			public.model_version_tags, \
			public.model_versions, \
			public.params, \
			public.registered_model_aliases, \
			public.registered_model_tags, \
			public.registered_models, \
			public.runs, \
			public.tags, \
			public.trace_info, \
			public.trace_request_metadata, \
			public.trace_tags \
			RESTART IDENTITY CASCADE;"


# For dev purposes, delete all artifact in S3-artifact-bucket
delete_mlflow_artifacts:
	@echo Deleting all objects in bucket : uzicorn-mlops-artifacts
	- awsv2 s3 rm s3://uzicorn-mlops-artifacts/ --recursive

delete_mlflow_data:
	$(MAKE) delete_mlflow_backend
	$(MAKE) delete_mlflow_artifacts

# For dev purposes, delete pycache
clear_pycache:
	cd ..
	find . -type d -name "__pycache__" -exec rm -r {} +


hard-delete-stack:
# Deletes all stacks, s3 files and cached builds
# 	Delete stacks
	@echo "Deleting all CloudFormation stacks..."
	- sam delete --stack-name mlops-stack --no-prompts
	@echo "-----------------------------------------"
# 	Delete S3 bucket files 
	@echo "Deleting all files from S3 bucket: mlops-serverless"
	- awsv2 s3 rm s3://mlops-serverless/infra --recursive
	@echo "-----------------------------------------"
#	Delete cached files
	@echo "Cleaning .aws-sam build directories..."
	- rm -rf $(WORKDIR)/infra/.aws-sam

# ☠️
order66:
	$(MAKE) delete_mlflow_backend
	$(MAKE) clean_training_artifacts_and_backend
	$(MAKE) clear_pycache
	$(MAKE) hard-delete-stack
