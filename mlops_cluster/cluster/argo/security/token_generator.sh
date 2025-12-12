# bin/bash 

# Create a token for the "default" service account linked to the argo namespace

argo_namespace="argo" 

# 1 create a role
kubectl delete role custom-argo-role 
# kubectl apply -n "$argo_namespace" -f cluster/argo/security/role_policy.yaml

# 2 Create service account
kubectl delete serviceaccount custom-service-account
# kubectl create sa custom-service-account -n "$argo_namespace" || true

# 3 Bind role to namespace 
# Note : this works with -f because namespace is hardcoded to "argo"
#        Otherwise, use <<EOF and the variable argo_namespace (flemme)
kubectl delete rolebinding custom-role-binding 
# kubectl apply -n "$argo_namespace" -f cluster/argo/security/role_binding.yaml

# 4 Create Token 
kubectl delete secret custom-service-account-token
# kubectl apply -n argo -f cluster/argo/security/create_token.yaml 

# 5 Get token 
# kubectl -n argo get secret custom-service-account-token -o jsonpath='{.data.token}' | base64 -d