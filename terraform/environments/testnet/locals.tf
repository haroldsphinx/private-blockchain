locals {
  project_name = trimspace(var.project_name) != "" ? var.project_name : "zama-pevm-testnet"

  common_tags = merge(
    {
      Project     = local.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )

  ssh_public_key = trimspace(var.ssh_public_key) != "" ? trimspace(var.ssh_public_key) : (
    trimspace(var.ssh_public_key_path) != "" ? trimspace(file(var.ssh_public_key_path)) : ""
  )

  cloud_init_raw = trimspace(var.cloud_init_file) != "" ? templatefile(var.cloud_init_file, {
    network_params    = trimspace(file("${path.module}/../../kurtosis/network_params.yaml"))
    argocd_values     = trimspace(file("${path.module}/../../k8s/argocd/argocd-values.yaml"))
    observability_app = trimspace(file("${path.module}/../../k8s/argocd/apps/observability.yaml"))
    ingress_manifest  = trimspace(file("${path.module}/../../k8s/ingress/ingress.yaml"))
  }) : ""
}
