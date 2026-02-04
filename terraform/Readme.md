# Terraform

Provisions 3 blockchain VMs + 1 monitoring VM on AWS.

```sh
cd terraform/environments/testnet
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars

terraform init
terraform apply
```

Set `ssh_public_key_path` or `ssh_public_key` in tfvars. Set `bootnode_pubkey` after running `scripts/generate-genesis.sh`.
