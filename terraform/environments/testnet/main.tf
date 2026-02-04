resource "aws_key_pair" "this" {
  count      = local.ssh_public_key != "" ? 1 : 0
  key_name   = var.key_pair_name
  public_key = local.ssh_public_key
}

locals {
  resolved_key_pair_name = local.ssh_public_key != "" ? aws_key_pair.this[0].key_name : (
    trimspace(var.key_pair_name) != "" ? var.key_pair_name : null
  )
}

data "cloudinit_config" "blockchain" {
  for_each      = var.blockchain_nodes
  gzip          = true
  base64_encode = true

  part {
    content_type = "text/cloud-config"
    content      = local.blockchain_cloud_init[each.key]
  }
}

data "cloudinit_config" "monitoring" {
  gzip          = true
  base64_encode = true

  part {
    content_type = "text/cloud-config"
    content      = local.monitoring_cloud_init_raw
  }
}

module "blockchain_instance" {
  for_each      = var.blockchain_nodes
  source        = "../../modules/compute"
  name          = format("%s-%s-%s", local.project_name, each.key, var.environment)
  ami           = var.ami_id
  instance_type = each.value.instance_type
  subnet_id     = aws_subnet.public.id
  security_group_ids = [
    aws_security_group.blockchain.id,
  ]

  associate_public_ip_address = false
  root_volume_size            = each.value.root_volume_size
  user_data_base64            = data.cloudinit_config.blockchain[each.key].rendered
  environment                 = var.environment
  tags = merge(local.common_tags, {
    Role = each.value.role
  })

  key_pair_name = local.resolved_key_pair_name
}

module "monitoring_instance" {
  source        = "../../modules/compute"
  name          = format("%s-monitoring-%s", local.project_name, var.environment)
  ami           = var.ami_id
  instance_type = var.monitoring_instance_type
  subnet_id     = aws_subnet.public.id
  security_group_ids = [
    aws_security_group.monitoring.id,
  ]

  associate_public_ip_address = false
  root_volume_size            = var.monitoring_root_volume_size
  user_data_base64            = data.cloudinit_config.monitoring.rendered
  environment                 = var.environment
  tags                        = local.common_tags

  key_pair_name = local.resolved_key_pair_name
}

resource "aws_eip" "blockchain" {
  for_each = var.blockchain_nodes
  domain   = "vpc"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-${each.key}-eip"
    },
  )
}

resource "aws_eip" "monitoring" {
  domain = "vpc"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-monitoring-eip"
    },
  )
}

resource "aws_eip_association" "blockchain" {
  for_each      = var.blockchain_nodes
  instance_id   = module.blockchain_instance[each.key].instance_id
  allocation_id = aws_eip.blockchain[each.key].id
}

resource "aws_eip_association" "monitoring" {
  instance_id   = module.monitoring_instance.instance_id
  allocation_id = aws_eip.monitoring.id
}

output "blockchain_nodes" {
  description = "Public and private IPs of blockchain nodes."
  value = {
    for name, node in var.blockchain_nodes : name => {
      public_ip  = aws_eip.blockchain[name].public_ip
      private_ip = module.blockchain_instance[name].private_ip
      role       = node.role
    }
  }
}

output "monitoring_public_ip" {
  description = "Elastic IP of the monitoring instance."
  value       = aws_eip.monitoring.public_ip
}

output "monitoring_private_ip" {
  description = "Private IP of the monitoring instance."
  value       = module.monitoring_instance.private_ip
}

output "bootnode_eip" {
  value = aws_eip.blockchain["node-1"].public_ip
}
