.ONESHELL:

# Global variables
CLUSTER_CONFIG_PATH=cluster/cluster.yaml

KEYNAME=/home/uzicorn/code/mlops/experiment_tracking/secret/test-key-pair.pem

AUTOSCALER_VALUES_PATH=cluster/autoscaler/auto_scaler_values.yaml

JH_VALUES_PATH=cluster/jupyterhub/values.yaml
JH_NAMESPACE=jupyterhub

ARGO_NAMESPACE=argo
ARGO_VALUES_PATH=cluster/argo/values.yaml

ecr_repo_name=mlops_poc

IRIS_NAMESPACE=iris
IRIS_VALUES_PATH=cluster/argo/workflows/iris.yaml
#----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

create_cluster:
	eksctl create cluster -f $(CLUSTER_CONFIG_PATH)
	kubectl apply -f gp3_storage_class.yaml
	kubectl delete storageclass gp2

update_node_group:
	eksctl update nodegroup -f $(CLUSTER_CONFIG_PATH)

list_ec2:
	awsv2 ec2 describe-instances \
  		--filters "Name=tag:eks:cluster-name,Values=$$(eksctl get cluster -o json | jq -r '.[].Name')" \
				  "Name=instance-state-name,Values=running" \
		--query   "Reservations[].Instances[].\
				  {InstanceId:InstanceId,Type:InstanceType,PrivateIP:PrivateIpAddress,\
				   PublicIP:PublicIpAddress,State:State.Name,ssh:KeyName,\
				   SecurityGroups:SecurityGroups[*].{ID:GroupId,Name:GroupName}\
				}" \
		--output yaml

connect_ec2:
	ssh -i $(KEYNAME) ec2-user@51.44.241.164

list_nodes:
	kubectl get nodes -o wide

list_pods:
	clear
	kubectl get pods -A \
	-o custom-columns=\
	RELEASE_NAME:.metadata.labels.app\\.kubernetes\\.io/instance,\
	NAMESPACE:.metadata.namespace,\
	POD_NAME:.metadata.name,\
	CREATED:.metadata.creationTimestamp,\
	IP:.status.podIP,\
	NODE:.spec.nodeName,\
	READY:.status.containerStatuses[*].ready,\
	STATUS:.status.phase | python3 pods_format.py

release_autoscaler:
	helm repo add --force-update autoscaler https://kubernetes.github.io/autoscaler
	helm repo update
	helm upgrade --install auto-scaler-release \
		autoscaler/cluster-autoscaler \
		--namespace kube-system \
		--values $(AUTOSCALER_VALUES_PATH)

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

#	Update/Create kube secret "ecr-pull-secret"
	echo - Updating ecr-pull-secret
	kubectl delete secret generic ecr-pull-secret -n iris --ignore-not-found=true
	kubectl create secret generic ecr-pull-secret -n iris \
		--from-file=.dockerconfigjson="/home/uzicorn/.docker/config.json" \
		--type=kubernetes.io/dockerconfigjson

#   Build and tag local image
	echo - Building iris image locally 
	docker build -q -t $$image_name:$$tag cluster/iris/.
#   Push to ECR
	echo - Pushing iris image to ecr repo : $(ecr_repo_name)
	docker push $$image_name:$$tag
#	Helm release : Container uses ECR image and ecr-pull-secret credentials
	echo - Helm release ...  
	repository=$$account_id.dkr.ecr.eu-west-3.amazonaws.com/$(ecr_repo_name)
	helm upgrade -n $(IRIS_NAMESPACE) --create-namespace --install iris-release ./cluster/iris --set image.repository=$$repository
#   Cleanup
	echo - Cleaning local docker repository
	echo - Deleting $$image_name:$$tag
	docker rmi $$image_name


#--------------
# dev helpers |
#--------------
delete_ecr_images:
	echo - Deleting all images in ECR repository $(ecr_repo_name)
	awsv2 ecr list-images --repository-name $(ecr_repo_name) --query imageIds | jq . > images_to_delete
	if [ "$$(jq length images_to_delete)" = 0 ]; then
		echo "There are no images in the repo"
	else
		awsv2 ecr batch-delete-image --repository-name $(ecr_repo_name) --image-ids file://images_to_delete
	fi
	rm images_to_delete
