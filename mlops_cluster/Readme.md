This project is a small MLOps proof of concept that provisions an EKS cluster and deploys a sample ML workload (Iris classification), along with JupyterHub, Argo Workflows, and a cluster autoscaler.

## Project overview

- **Goal**: Provision an AWS EKS cluster and run an end-to-end ML workload using Argo workflows and a custom Iris model application.
- Main components:
  - EKS cluster and storage configuration under `cluster/cluster.yaml` and `gp3_storage_class.yaml`.
  - Helm-based deployments for autoscaler, JupyterHub, Argo Workflows, and a custom Iris chart.

## Structure

- **cluster/**
  - `cluster.yaml`: EKS cluster definition for `eksctl`.
  - `gp3_storage_class.yaml`: Custom storage class configuration.  
  - `autoscaler/auto_scaler_values.yaml`: Values for the Kubernetes cluster autoscaler Helm chart.
  - `jupyterhub/*`: Values and security scripts for a JupyterHub deployment on EKS.
  - `argo/*`: Values, security, and example workflows for Argo Workflows.
  - `iris/*`: Custom Helm chart and Docker image for an Iris ML app (ingestion, training, and deployment).

## Makefile targets

- **Cluster lifecycle**:
  - `create_cluster`, `update_node_group`, `hard-delete-all-ressources` to create, update, and fully destroy the EKS environment.
- **Monitoring and helpers**:
  - `list_ec2`, `connect_ec2`, `list_nodes`, `list_pods`, `list_stacks`, `instances_counter.sh` for basic cluster and EC2 inspection.
- **Helm releases**:
  - `release_autoscaler`, `release_jupyterhub`, `release_argo` to install core operational services.
- **Iris ML app**:
  - `release_iris`, `update_iris`, `uninstall-iris`, `create-iris-policy`, `create-iris-sa`, `delete_ecr_images` to build, push, and deploy the Iris Docker image from `cluster/iris` via ECR and Helm.

## Basic usage

- **Create cluster**: `make create_cluster` (requires configured AWS CLI, eksctl, kubectl, helm, and awsv2).
- **Install core services**: run `make release_autoscaler`, `make release_jupyterhub`, and `make release_argo` after the cluster is ready. 
- **Deploy Iris app**: `make release_iris` to build the image, push to ECR, create IAM resources, and deploy the chart.
- **Tear down**: `make hard-delete-all-ressources` to remove Helm releases, IAM resources, ECR repo, and the EKS cluster.

## Structure 
```bash
.
├── cluster
│   ├── argo
│   │   ├── default.yaml
│   │   ├── security
│   │   │   ├── create_token.yaml
│   │   │   ├── role_binding.yaml
│   │   │   ├── role_policy.yaml
│   │   │   └── token_generator.sh
│   │   ├── values.yaml
│   │   └── workflows
│   │       ├── ingest_classification.yaml
│   │       └── train_classification.yaml
│   ├── autoscaler
│   │   └── auto_scaler_values.yaml
│   ├── cluster.yaml
│   ├── gp3_storage_class.yaml
│   ├── iris
│   │   ├── app
│   │   │   ├── ingestion
│   │   │   │   ├── ingest.py
│   │   │   │   ├── iris_connector.py
│   │   │   │   └── utils.py
│   │   │   ├── __init__.py
│   │   │   ├── requirements.txt
│   │   │   ├── test_secrets.py
│   │   │   └── training
│   │   │       ├── train_iris_classification.py
│   │   │       └── utils.py
│   │   ├── Chart.yaml
│   │   ├── Dockerfile
│   │   ├── security
│   │   │   └── iris_policy.yaml
│   │   ├── templates
│   │   │   └── deployment.yaml
│   │   └── values.yaml
│   └── jupyterhub
│       ├── defaults.yaml
│       ├── security
│       │   ├── jupyterhub_ip_ranges.json
│       │   └── restrict_jupyter_ips.sh
│       └── values.yaml
├── instances_counter.sh
├── Makefile
├── pods_format.py
└── Readme.md
```