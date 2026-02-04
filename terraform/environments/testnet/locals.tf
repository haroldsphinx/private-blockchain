locals {
  project_name = trimspace(var.project_name) != "" ? var.project_name : "zama-pevm-testnet"
  repo_root    = "${path.module}/../../.."

  common_tags = merge(
    {
      Project     = local.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )

  ssh_public_key = trimspace(var.ssh_public_key) != "" ? trimspace(var.ssh_public_key) : (
    trimspace(var.ssh_public_key_path) != "" ? trimspace(file(pathexpand(var.ssh_public_key_path))) : ""
  )

  monitoring_cloud_init_raw = trimspace(var.monitoring_cloud_init_file) != "" ? templatefile(var.monitoring_cloud_init_file, {
    gmail_app_password = var.gmail_app_password
  }) : ""

  # Bootnode is always node-1
  bootnode_name = "node-1"
  bootnode_eip  = aws_eip.blockchain[local.bootnode_name].public_ip

  blockchain_cloud_init = {
    for name, node in var.blockchain_nodes : name => templatefile(var.blockchain_cloud_init_file, {
      node_name             = name
      node_role             = node.role
      own_eip               = aws_eip.blockchain[name].public_ip
      bootnode_eip          = local.bootnode_eip
      bootnode_pubkey       = var.bootnode_pubkey
      bootnode_enr          = var.bootnode_enr
      monitoring_private_ip = module.monitoring_instance.private_ip
      github_repo           = var.github_repo
    })
  }
}
