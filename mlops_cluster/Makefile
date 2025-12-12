.ONESHELL:

CLUSTER_CONFIG_PATH=cluster/cluster.yaml
KEYNAME=/home/uzicorn/code/mlops/experiment_tracking/secret/test-key-pair.pem
AUTOSCALER_VALUES_PATH=cluster/autoscaler/auto_scaler_values.yaml
JH_VALUES_PATH=cluster/jupyterhub/values.yaml
JH_NAMESPACE=jupyterhub
ARGO_NAMESPACE=argo
ARGO_VALUES_PATH=cluster/argo/values.yaml

deploy_cluster:
	eksctl create cluster -f $(CLUSTER_CONFIG_PATH)
	kubectl apply -f gp3_storage_class.yaml
	kubectl delete storageclass gp2

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
	ssh -i $(KEYNAME) ec2-user@35.180.66.237

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