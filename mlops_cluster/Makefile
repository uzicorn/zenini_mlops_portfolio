.ONESHELL:

#-----------------------+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
# Global Variables |
#-------------------
#-- cluster
 CLUSTER_CONFIG_PATH=cluster/cluster.yaml
 CLUSTER_NAME=my-eks-cluster
#-- ssh to ec2
 KEYNAME=/home/uzicorn/code/mlops/experiment_tracking/secret/test-key-pair.pem
#-- autoscaler
 AUTOSCALER_VALUES_PATH=cluster/autoscaler/auto_scaler_values.yaml
#-- jupyterhub
 JH_VALUES_PATH=cluster/jupyterhub/values.yaml
 JH_NAMESPACE=jupyterhub
#-- argo
 ARGO_NAMESPACE=argo
 ARGO_VALUES_PATH=cluster/argo/values.yaml
#-- custom chart images repository
 ecr_repo_name=mlops_poc
#-- custom chart iris
 IRIS_NAMESPACE=iris
 IRIS_VALUES_PATH=cluster/argo/workflows/iris.yaml
#-- ECR Pull image credentials are stored in docker config, they are passed to the custom charts template 
 DOCKER_CONFIG_FILE=/home/uzicorn/.docker/config.json
#----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

#                                     -----------------------------
#-------------------------------------| Cluster Creation | Update |-------------------------------------------------
#                                     -----------------------------
create_cluster:
# 	Create cluster
	eksctl create cluster -f $(CLUSTER_CONFIG_PATH)
# 	Upgrade storage class
	kubectl apply -f gp3_storage_class.yaml
	kubectl delete storageclass gp2
# 	Enable OICD  
	eksctl utils associate-iam-oidc-provider --cluster $(CLUSTER_NAME) --approve

update_node_group:
	eksctl update nodegroup -f $(CLUSTER_CONFIG_PATH)

#					                       --------------
#------------------------------------------| Monitoring |-----------------------------------------------------------
#					                       --------------

list_ec2:
	awsv2 ec2 describe-instances \
  		--filters "Name=tag:eks:cluster-name,Values=$(CLUSTER_NAME)" \
				  "Name=instance-state-name,Values=running" \
		--query \
		"Reservations[].Instances[].\
		{InstanceId:InstanceId,Type:InstanceType,PrivateIP:PrivateIpAddress,\
		PublicIP:PublicIpAddress,State:State.Name,ssh:KeyName,\
		SecurityGroups:SecurityGroups[*].{ID:GroupId,Name:GroupName}\
		}" --output yaml

Ec2PublicIp:=""
connect_ec2:
	if [ "$(Ec2PublicIp)" = "" ]; then echo "command usage : make connect_ec2 Ec2PublicIp=<public_ip>"
	else ssh -i $(KEYNAME) ec2-user@$(Ec2PublicIp)
	fi

list_nodes:
	kubectl get nodes -o wide

namespace :=
list_pods:
# 	Usage : make list_pods
#   	    make list_pods namespace=argo
	clear
	kubectl get pods $$(if [ $(namespace) = "" ]; then echo "-A" ;else echo "-n $(namespace)"; fi) \
	-o custom-columns=\
	"\
		RELEASE_NAME:.metadata.labels.app\\.kubernetes\\.io/instance,\
		NAMESPACE:.metadata.namespace,\
		POD_NAME:.metadata.name,\
		CREATED:.metadata.creationTimestamp,\
		IP:.status.podIP,\
		NODE:.spec.nodeName,\
		READY:.status.containerStatuses[*].ready,\
		STATUS:.status.phase" \
	| python3 pods_format.py


list_stacks:
	awsv2 cloudformation describe-stacks --query 'Stacks[].[StackName, Description, StackStatus]' | jq .
#					                       -----------------
#------------------------------------------| Helm Releases |--------------------------------------------------------
#					                       -----------------

#  ----------------------
#  ├── Autoscaler release 
#  ----------------------
release_autoscaler:
	helm repo add --force-update autoscaler https://kubernetes.github.io/autoscaler
	helm repo update
	helm upgrade --install auto-scaler-release \
		autoscaler/cluster-autoscaler \
		--namespace kube-system \
		--values $(AUTOSCALER_VALUES_PATH)

# ---------------------
# ├──Jupyterhub release
# ---------------------
restrict_jupyter_ips:
	bash cluster/jupyterhub/security/restrict_jupyter_ips.sh

release_jupyterhub:
	helm repo add --force-update jupyterhub https://hub.jupyter.org/helm-chart/
	helm repo update
	helm upgrade --install jupyterhub-release \
		jupyterhub/jupyterhub \
		--create-namespace \
		--namespace $(JH_NAMESPACE) \
		--values $(JH_VALUES_PATH)
#   Let the pods run before restricting IP (Not fit for production, 3s are arbitrary)
	sleep 3
	$(MAKE) restrict_jupyter_ips

# ---------------
# ├──Argo release
# ---------------
release_argo:
	helm repo add argo https://argoproj.github.io/argo-helm
	helm repo update
	helm upgrade --install argo-release \
		argo/argo-workflows \
		--create-namespace \
		--namespace $(ARGO_NAMESPACE) \
		--values $(ARGO_VALUES_PATH)

argo_connect_server:
	echo "Browse http://localhost:2746/"
	kubectl port-forward svc/argo-release-argo-workflows-server 2746:2746 -n argo

argo_create_token:
	bash cluster/argo/security/token_generator.sh

# ---------------
# ├──IRIS release
# ---------------

# Attempt to fully deploy a custom chart representing a machine learning app (module)
# The deployed app is the exact replica of the portfolio's ./experiment_tracking but now integrated in an EKS cluster
# with custom AWS-policies, compute and memory allocation and integrations with various AWS ressources (EKS, S3, AWS-Secrets, lambda) 
create-iris-policy:
	echo - Deleting iris iam policy if it exists
	account_id=$$(awsv2 sts get-caller-identity --query 'Account' --output text)
	awsv2 iam delete-policy --policy-arn arn:aws:iam::$$account_id:policy/iris-policy \
		2>/dev/null	|| echo iris policy does not exists
	
	echo - Creating iris-policy
	awsv2 iam create-policy \
		--policy-name iris-policy \
		--policy-document file://cluster/iris/security/iris_policy.yaml

# 	Command to find the policy ARN : awsv2 iam list-policies --query "Policies[?PolicyName=='iris-policy']"
# 	Command to update  the  policy : awsv2 iam create-policy-version --policy-arn $$account_id:policy/iris-policy \ 
# 									  --policy-document <file> --set-as-default 

create-iris-sa:
	echo - Deleting iris-sa if it exists
	eksctl delete iamserviceaccount --namespace $(IRIS_NAMESPACE) --name iris-sa --cluster $(CLUSTER_NAME)
	
	echo - Creating iris-sa
	account_id=$$(awsv2 sts get-caller-identity --query 'Account' --output text)
	eksctl create iamserviceaccount \
		--cluster $(CLUSTER_NAME) \
		--namespace $(IRIS_NAMESPACE) \
		--name iris-sa \
		--attach-policy-arn arn:aws:iam::$$account_id:policy/iris-policy \
		--approve

release_iris:
#   AWS-ECR variables 
#	(ecr_repo_name is a make variable, not shell)
	tag=latest
	account_id=$$(awsv2 sts get-caller-identity --query 'Account' --output text)
	endpoint=$$account_id.dkr.ecr.eu-west-3.amazonaws.com
	image_name=$$endpoint/$(ecr_repo_name)

#   Docker authentication  
	echo - Docker authentication ...
	awsv2 ecr get-login-password | docker login --username AWS --password-stdin $$endpoint

#   Build and tag local image
	echo - Building iris image locally 
	docker build -q -t $$image_name:$$tag cluster/iris/.

#   Push to ECR
	echo - Pushing iris image to ecr repo : $(ecr_repo_name)
	docker push -q $$image_name:$$tag

#	Create IRIS NAMESPACE
	echo - Create iris namespace
	kubectl create namespace $(IRIS_NAMESPACE)

#   Update/Create kube secret "ecr-pull-secret"
	echo - Updating ecr-pull-secret
	kubectl delete secret generic ecr-pull-secret -n $(IRIS_NAMESPACE) --ignore-not-found=true
	kubectl create secret generic ecr-pull-secret -n $(IRIS_NAMESPACE) \
		--from-file=.dockerconfigjson=$(DOCKER_CONFIG_FILE) \
		--type=kubernetes.io/dockerconfigjson

#	Create/update aws policy for AWS Secrets  
	$(MAKE) create-iris-policy

#	Create/update iris service account
	$(MAKE) create-iris-sa

#	Release iris pod linked with a service-account that has ECR and secrets permissions
#	Check : cluster/iris/templates/deployment.yaml and cluster/iris/security/aws_policy.yaml
	echo - Helm release ...  
	repository=$$account_id.dkr.ecr.eu-west-3.amazonaws.com/$(ecr_repo_name)
	helm upgrade -n $(IRIS_NAMESPACE) \
		--install iris-release ./cluster/iris \
		--set image.repository=$$repository \
		--set aws.account-id=$$account_id

#   Cleanup
	echo - Cleaning local docker repository : Deleting $$image_name:$$tag
	docker rmi $$image_name >/dev/null

uninstall-iris:
# 	dev helper to drop
	kubectl delete namespace iris
	eksctl delete iamserviceaccount --namespace $(IRIS_NAMESPACE) --name iris-sa --cluster $(CLUSTER_NAME)
	kubectl delete secret generic ecr-pull-secret -n $(IRIS_NAMESPACE) --ignore-not-found=true
	account_id=$$(awsv2 sts get-caller-identity --query 'Account' --output text)
	awsv2 iam delete-policy --policy-arn arn:aws:iam::$$account_id:policy/iris-policy \
		2>/dev/null	|| echo iris policy does not exists

update_iris:
	echo - Update release : IRIS
	account_id=$$(awsv2 sts get-caller-identity --query 'Account' --output text)
	repository=$$account_id.dkr.ecr.eu-west-3.amazonaws.com/$(ecr_repo_name)
	helm upgrade -n $(IRIS_NAMESPACE) \
		--install iris-release ./cluster/iris \
		--set image.repository=$$repository \
		--set aws.account-id=$$account_id
#					                       ---------------
#------------------------------------------| Dev Helpers |----------------------------------------------------------
#					                       ---------------
delete_ecr_images:
	echo - Deleting all images in ECR repository $(ecr_repo_name)
	awsv2 ecr list-images --repository-name $(ecr_repo_name) --query imageIds | jq . > images_to_delete
	if [ "$$(jq length images_to_delete)" = 0 ]; then
		echo "There are no images in the repo"
	else
		awsv2 ecr batch-delete-image --repository-name $(ecr_repo_name) --image-ids file://images_to_delete
	fi
	rm images_to_delete

release :=""
namespace :=""
kill-release:
	if [ "$(namespace)" = "" ] || ["$(release)" = "" ]; 
	then echo "Usage : make kill-release namespace=<namespace> release=<release>"; exit 
	fi 
	echo - Uninstalling the helm release named : $(release) 
	helm uninstall $(release) -n $(namespace) \
		2>/dev/null	|| echo "release '$(release)' does not exists"
	
	echo - Deleting all that has been created in the namespace
	kubectl delete namespace $(namespace) \
		2>/dev/null	|| echo "namespace '$(namespace)' does not exists"
	
	echo - Deleting IRSA cloud formation stack related to to namespace '$(namespace)'
	if [ "$$(eksctl get iamserviceaccount -c $(CLUSTER_NAME) --namespace $(namespace) | tr -d '\n')" = "No iamserviceaccounts found" ]; then
		echo "there is No iamserviceaccounts linked to namespace '$(namespace)'"
	else 
		eksctl delete iamserviceaccount --namespace $(namespace) --name iris-sa --cluster $(CLUSTER_NAME)
	fi
	