locals {
  sanitized_public_key = var.public_key != null ? trimspace(var.public_key) : ""
  create_key_pair      = length(local.sanitized_public_key) > 0
  key_pair_name        = local.create_key_pair ? coalesce(var.key_pair_name, "${var.name}-key") : var.key_pair_name
}

resource "aws_key_pair" "this" {
  count = local.create_key_pair ? 1 : 0

  key_name   = local.key_pair_name
  public_key = local.sanitized_public_key
}

resource "aws_instance" "this" {
  ami           = var.ami
  instance_type = var.instance_type
  subnet_id     = var.subnet_id

  associate_public_ip_address = var.associate_public_ip_address
  vpc_security_group_ids      = var.security_group_ids

  key_name = local.create_key_pair ? aws_key_pair.this[0].key_name : var.key_pair_name

  user_data_base64 = length(trimspace(var.user_data_base64)) > 0 ? var.user_data_base64 : null

  root_block_device {
    volume_size = var.root_volume_size
    volume_type = var.volume_type
  }

  tags = merge(
    {
      Name        = var.name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )
}
