variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "label applied to resources"
  type        = string
  default     = "zama-pevm-testnet"
}

variable "environment" {
  description = "environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "cidr block for the vpc"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "cidr block for the public subnet"
  type        = string
  default     = "10.20.1.0/24"
}

variable "availability_zone" {
  description = "availability zone for subnet placement"
  type        = string
  default     = "us-east-1a"
}

variable "allowed_ingress_cidrs" {
  description = "cidr blocks permitted to reach exposed service ports"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "ssh_allowed_cidrs" {
  description = "cidr blocks permitted for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "instance_type" {
  description = "instance type for the testnet host (needs 4+ vCPU, 16GB+ RAM for minikube + k8s workloads)"
  type        = string
  default     = "t3.xlarge"
}

variable "ami_id" {
  description = "ami identifier for the service host (Ubuntu 22.04)"
  type        = string
  default     = "ami-04b70fa74e45c3917"
}

variable "associate_public_ip" {
  description = "whether the instance receives a public IP address"
  type        = bool
  default     = true
}

variable "root_volume_size" {
  description = "root volume size in GiB"
  type        = number
  default     = 80
}

variable "ssh_public_key_path" {
  description = "path to an ssh public key to register. leave blank to skip key creation"
  type        = string
  default     = ""
}

variable "ssh_public_key" {
  description = "inline ssh public key content. takes precedence over ssh_public_key_path"
  type        = string
  default     = ""
}

variable "key_pair_name" {
  description = "name for the key pair"
  type        = string
  default     = "zama"
}

variable "cloud_init_file" {
  description = "Path to a cloud-init configuration file."
  type        = string
  default     = "./files/zama-pevm-testnet-cloud-init.yml.tmpl"
}

variable "tags" {
  description = "Additional tags applied to resources."
  type        = map(string)
  default     = {}
}
