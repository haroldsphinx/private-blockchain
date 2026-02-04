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

resource "aws_security_group" "blockchain" {
  name_prefix = "${local.project_name}-blockchain-sg-"
  description = "Blockchain node: geth, lighthouse, blockscout"
  vpc_id      = aws_vpc.main.id

  # SSH
  ingress {
    description = "SSH"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = var.ssh_allowed_cidrs
  }

  # Geth P2P (TCP + UDP)
  ingress {
    description = "Geth P2P TCP"
    protocol    = "tcp"
    from_port   = 30303
    to_port     = 30303
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Geth P2P UDP"
    protocol    = "udp"
    from_port   = 30303
    to_port     = 30303
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Geth RPC/WS
  ingress {
    description = "Geth JSON-RPC"
    protocol    = "tcp"
    from_port   = 8545
    to_port     = 8545
    cidr_blocks = var.allowed_ingress_cidrs
  }
  ingress {
    description = "Geth WebSocket"
    protocol    = "tcp"
    from_port   = 8546
    to_port     = 8546
    cidr_blocks = var.allowed_ingress_cidrs
  }

  # Geth metrics
  ingress {
    description = "Geth metrics"
    protocol    = "tcp"
    from_port   = 6060
    to_port     = 6060
    cidr_blocks = var.allowed_ingress_cidrs
  }

  # Lighthouse P2P (TCP + UDP + QUIC)
  ingress {
    description = "Lighthouse P2P TCP"
    protocol    = "tcp"
    from_port   = 9000
    to_port     = 9000
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Lighthouse P2P UDP"
    protocol    = "udp"
    from_port   = 9000
    to_port     = 9000
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Lighthouse QUIC"
    protocol    = "udp"
    from_port   = 9001
    to_port     = 9001
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Lighthouse HTTP API
  ingress {
    description = "Lighthouse HTTP API"
    protocol    = "tcp"
    from_port   = 5052
    to_port     = 5052
    cidr_blocks = var.allowed_ingress_cidrs
  }

  # Lighthouse metrics
  ingress {
    description = "Lighthouse beacon metrics"
    protocol    = "tcp"
    from_port   = 5054
    to_port     = 5054
    cidr_blocks = var.allowed_ingress_cidrs
  }
  ingress {
    description = "Lighthouse validator metrics"
    protocol    = "tcp"
    from_port   = 5064
    to_port     = 5064
    cidr_blocks = var.allowed_ingress_cidrs
  }

  # Blockscout
  ingress {
    description = "Blockscout"
    protocol    = "tcp"
    from_port   = 4000
    to_port     = 4000
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
      Name = "${local.project_name}-blockchain-sg"
    },
  )
}

resource "aws_security_group" "monitoring" {
  name_prefix = "${local.project_name}-monitoring-sg-"
  description = "Monitoring: Grafana, Prometheus, AlertManager"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = var.ssh_allowed_cidrs
  }

  ingress {
    description = "Grafana"
    protocol    = "tcp"
    from_port   = 3000
    to_port     = 3000
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description = "Prometheus"
    protocol    = "tcp"
    from_port   = 9090
    to_port     = 9090
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description = "AlertManager"
    protocol    = "tcp"
    from_port   = 9093
    to_port     = 9093
    cidr_blocks = var.allowed_ingress_cidrs
  }

  ingress {
    description     = "Loki push from Telescope"
    protocol        = "tcp"
    from_port       = 3100
    to_port         = 3100
    security_groups = [aws_security_group.blockchain.id]
  }

  ingress {
    description     = "Prometheus remote write from Telescope"
    protocol        = "tcp"
    from_port       = 9090
    to_port         = 9090
    security_groups = [aws_security_group.blockchain.id]
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
      Name = "${local.project_name}-monitoring-sg"
    },
  )
}
