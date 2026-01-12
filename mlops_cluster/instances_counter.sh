#!/bin/bash
# cost_checker.sh - Check running AWS resources that incur costs
# Run with: bash cost_checker.sh

echo "Resource Type | Count (Running/Active)"
echo "--------------|-----------------------"

# 1. EC2 Instances (per-second billing)
ec2_count=$(awsv2 ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query "length(Reservations[].Instances[])" --output text)
printf "EC2 Instances  | %s\n" "$ec2_count"

# 2. EKS Clusters (control plane $0.10/hr)
eks_count=$(awsv2 eks list-clusters --query "clusters[?contains(@, 'my-eks-cluster')]" --output text | wc -l)
printf "EKS Clusters   | %s\n" "$eks_count"

# 3. ECR Repositories with images (storage $0.10/GB/month)
ecr_count=$(awsv2 ecr describe-repositories --repository-names "mlops_poc" \
  --query "repositories[?imageTagMutability=='MUTABLE'].repositoryName" --output text | wc -l)
printf "ECR Repos     | %s\n" "$ecr_count"

# 4. Elastic Load Balancers (NLB/ALB ~$0.0225/hr)
elb_count=$(awsv2 elb describe-load-balancers --query "length(LoadBalancerDescriptions[])" --output text)
nlb_count=$(awsv2 elbv2 describe-load-balancers --query "length(LoadBalancers[])" --output text)
total_elb=$((elb_count + nlb_count))
printf "Load Balancers | %s\n" "$total_elb"

# 5. RDS DB Instances (if any)
rds_count=$(awsv2 rds describe-db-instances \
  --query "length(DBInstances[?DBInstanceStatus=='available'])[]" --output text)
printf "RDS DBs       | %s\n" "$rds_count"

# 6. S3 Buckets (if you created any for ML data)
s3_count=$(awsv2 s3api list-buckets --query "length(Buckets[])" --output text)
printf "S3 Buckets    | %s\n" "$s3_count"

# 7. CloudFormation Stacks (ACTIVE)
cf_count=$(awsv2 cloudformation list-stacks \
  --query "length(StackSummaries[?StackStatus=='CREATE_COMPLETE' || StackStatus=='UPDATE_COMPLETE'])[]" --output text)
printf "CF Stacks     | %s\n" "$cf_count"

echo ""
echo "🚨 DANGERS ($$):"
[ "$ec2_count" != "0" ] && echo "  - EC2 running (terminate: awsv2 ec2 terminate-instances)"
[ "$eks_count" != "0" ] && echo "  - EKS active (delete: eksctl delete cluster)"
[ "$ecr_count" != "0" ] && echo "  - ECR images (delete: make delete_ecr_images)"
[ "$total_elb" != "0" ] && echo "  - Load Balancers (check: awsv2 elbv2 describe-load-balancers)"
