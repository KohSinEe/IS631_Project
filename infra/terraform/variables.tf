variable "project_name" {
  description = "Prefix used in AWS resource names"
  type        = string
  default     = "fridgebuddy"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Optional existing EC2 key pair name for SSH"
  type        = string
  default     = ""
}

variable "admin_cidr" {
  description = "CIDR allowed to SSH into EC2"
  type        = string
  default     = "0.0.0.0/0"
}

variable "subnet_id" {
  description = "Optional subnet id. If empty, first subnet in default VPC is used"
  type        = string
  default     = ""
}

variable "repo_url" {
  description = "Git repository URL to clone on EC2"
  type        = string
}

variable "repo_branch" {
  description = "Git branch to deploy"
  type        = string
  default     = "main"
}

variable "secrets_manager_arn" {
  description = "Secrets Manager ARN containing app env vars (JSON or dotenv string)"
  type        = string
}

variable "cognito_user_pool_arn" {
  description = "Cognito User Pool ARN used by backend auth flows"
  type        = string
  default     = ""
}

variable "deploy_id" {
  description = "Unique ID per deploy (e.g. git commit SHA) — forces instance replacement on every deploy"
  type        = string
  default     = "manual"
}
