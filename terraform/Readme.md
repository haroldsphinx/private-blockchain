# Terraform

```sh
cd terraform/environments/testnet
terraform init
terraform plan -out plan.out
terraform apply
```

Provisions a VPC + EC2 instance (t3.xlarge) that bootstraps minikube, kurtosis, ArgoCD, and the full testnet via cloud-init.

Set an existing AWS key pair name via `key_pair_name` in `terraform.tfvars`, or provide `ssh_public_key_path` to create one.

AWS credentials via environment variables or default credential chain.
