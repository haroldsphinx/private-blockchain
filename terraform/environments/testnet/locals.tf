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

  cloud_init_raw = trimspace(var.cloud_init_file) != "" ? templatefile(var.cloud_init_file, {
    network_params = trimspace(file("${local.repo_root}/kurtosis/network_params.yaml"))
    repo_url       = var.repo_url
  }) : ""
}
