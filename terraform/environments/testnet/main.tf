data "cloudinit_config" "this" {
  gzip          = true
  base64_encode = true

  part {
    content_type = "text/cloud-config"
    content      = local.cloud_init_raw
  }
}

module "testnet_instance" {
  source        = "../../modules/compute"
  name          = format("%s-%s", local.project_name, var.environment)
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public.id
  security_group_ids = [
    aws_security_group.testnet.id,
  ]

  associate_public_ip_address = false
  root_volume_size            = var.root_volume_size
  user_data_base64            = data.cloudinit_config.this.rendered
  environment                 = var.environment
  tags                        = local.common_tags

  key_pair_name = trimspace(var.key_pair_name) != "" ? var.key_pair_name : null
  public_key    = local.ssh_public_key != "" ? local.ssh_public_key : null
}

resource "aws_eip" "testnet" {
  domain = "vpc"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-eip"
    },
  )
}

resource "aws_eip_association" "testnet" {
  instance_id   = module.testnet_instance.instance_id
  allocation_id = aws_eip.testnet.id
}

output "instance_public_ip" {
  description = "Elastic IP of the zama-pevm-testnet instance."
  value       = aws_eip.testnet.public_ip
}

output "instance_private_ip" {
  description = "Private IP of the zama-pevm-testnet instance."
  value       = module.testnet_instance.private_ip
}
