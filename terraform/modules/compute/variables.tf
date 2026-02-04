variable "name" {
  description = "base name for the instance"
  type        = string
}

variable "ami" {
  description = "ami to use for the instance"
  type        = string
}

variable "instance_type" {
  description = "instance type for the service host"
  type        = string
}

variable "subnet_id" {
  description = "subnet where the instance will be created"
  type        = string
}

variable "security_group_ids" {
  description = "security groups to associate with the instance"
  type        = list(string)
  default     = []
}

variable "associate_public_ip_address" {
  description = "whether to associate a public IP address with the instance"
  type        = bool
  default     = true
}

variable "user_data_base64" {
  description = "base64-encoded (gzipped) cloud-init payload"
  type        = string
  default     = ""
}

variable "root_volume_size" {
  description = "size of the root volume in GiB"
  type        = number
  default     = 20
}

variable "volume_type" {
  description = "root volume type"
  type        = string
  default     = "gp3"
}

variable "tags" {
  description = "tags to attach to created resources"
  type        = map(string)
  default     = {}
}

variable "environment" {
  description = "deployment environment tag value"
  type        = string
  default     = "dev"
}

variable "key_pair_name" {
  description = "existing key pair name to attach to the instance. ignored when public_key is provided"
  type        = string
  default     = null
}

variable "public_key" {
  description = "ssh public key material. when provided, a key pair will be created automatically"
  type        = string
  default     = null
}
