resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-vpc"
    },
  )
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-igw"
    },
  )
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-public-subnet"
      Tier = "public"
    },
  )
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-public-rt"
    },
  )
}

resource "aws_route" "internet_access" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "testnet" {
  name_prefix = "${local.project_name}-sg-"
  description = "Allow access to the zama-pevm-testnet and observability host."
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = var.ssh_allowed_cidrs
  }

  ingress {
    description = "Kurtosis EL nodes (rpc, ws, metrics, discovery)"
    protocol    = "tcp"
    from_port   = 32000
    to_port     = 32019
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description = "Kurtosis CL nodes (http, metrics, discovery)"
    protocol    = "tcp"
    from_port   = 33000
    to_port     = 33019
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description = "Kurtosis validator clients"
    protocol    = "tcp"
    from_port   = 34000
    to_port     = 34009
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description = "Kurtosis additional services (blockscout, grafana, prometheus, assertoor)"
    protocol    = "tcp"
    from_port   = 36000
    to_port     = 36019
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description = "Observability stack (grafana 3001, prometheus 9091, alertmanager 9093)"
    protocol    = "tcp"
    from_port   = 3001
    to_port     = 3001
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description = "Observability Prometheus"
    protocol    = "tcp"
    from_port   = 9091
    to_port     = 9091
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description = "AlertManager"
    protocol    = "tcp"
    from_port   = 9093
    to_port     = 9093
    cidr_blocks = var.allowed_ingress_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-sg"
    },
  )
}
