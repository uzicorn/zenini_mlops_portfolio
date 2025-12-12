# bin/bash
#
# CONTEXT : Jupyterhub Helm release --> Proxy pod --> load balancer <-- Security groups <----- "THIS SCRIPT"
#                                                           |                 |
#                                                         Users           authorize
#                                                           |                 |
#                                                          Ips <--------------+
#  
# DESCRIPTION : This script Update the authorized users who can access jupyterhub By locating and modifying 
#               jupyterhub's security group
# 
# Steps :                                                                    
#   1 - Get load balancer DNS from kubectl              
#   2 - Get load balancer security group ID from aws elb
#   3 - Get security group current inbound ip ranges    
#   4 - Revoke old ip ranges                            
#   5 - Update security group inbound ip range from jupyterhub_ip_ranges.json
# 
#------------------------------------------------------------------------------------+
# In production "cluster/jupyterhub/security/jupyterhub_ip_ranges.json" would point  |
# to an S3 file, it is in my opinion  the most easy way to keep users IP secure      |
# without complex security protocols                                                 |
#------------------------------------------------------------------------------------+

echo "###### IPS RESTRICTION SCRIPT ######"

# 1 Get load balancer DNS from kubectl
dns_query='{.items[0].status.loadBalancer.ingress[0].hostname}'
dns_load_balancer=$(kubectl get svc -n jupyterhub -l app.kubernetes.io/component=proxy-public -o jsonpath="$dns_query")
echo - Load balancer DNS : $dns_load_balancer

# 2 Get sg id from aws elb 
elb_query="LoadBalancerDescriptions[?DNSName=='$dns_load_balancer'].SecurityGroups[0]"
sg_id=$(awsv2 elb describe-load-balancers --query $elb_query --output text)
echo - Load balancer security group id : $sg_id

# 3 Get sg current inbound ips
ip_ranges_query='SecurityGroups[0].IpPermissions[?IpProtocol==`tcp`]'
current_ip_ranges=$(awsv2 ec2 describe-security-groups --group-ids $sg_id --query $ip_ranges_query --output json) 
echo "- Current jupyerhub authorized IPs are : 
        $current_ip_ranges"

# 4 Revoke old ip ranges 
awsv2 ec2 revoke-security-group-ingress --group-id "$sg_id" --ip-permissions "$current_ip_ranges" --no-cli-auto-prompt

# 5 Update sg inbound ip 
new_ip_range=$(cat cluster/jupyterhub/security/jupyterhub_ip_ranges.json | jq .)
echo "- New jupyerhub authorized IPs are : 
        $new_ip_range"
awsv2 ec2 authorize-security-group-ingress --group-id $sg_id --ip-permissions "$new_ip_range" --no-cli-auto-prompt
