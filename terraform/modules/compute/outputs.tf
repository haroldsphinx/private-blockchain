output "instance_id" {
  description = "Identifier of the created instance."
  value       = aws_instance.this.id
}

output "public_ip" {
  description = "Public IPv4 address of the instance."
  value       = aws_instance.this.public_ip
}

output "private_ip" {
  description = "Private IPv4 address of the instance."
  value       = aws_instance.this.private_ip
}

output "private_ip_cidr" {
  description = "Private IPv4 address in CIDR notation for security group rules."
  value       = "${aws_instance.this.private_ip}/32"
}

