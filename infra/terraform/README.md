# Terraform Demo Deployment (EC2 + Secrets Manager)

This template deploys a **single EC2 instance** for a low-cost school demo.

It configures:
- EC2 instance (Ubuntu)
- Security group (SSH + Streamlit + API)
- IAM role + instance profile
- IAM policy for Secrets Manager read access
- User data bootstrap script that:
  - installs Docker + Compose
  - clones this repo
  - fetches secrets from Secrets Manager
  - writes `.env`
  - runs `docker compose up -d --build`

## 1. Prepare Secrets Manager

Store your application environment in one secret as either:

- JSON object:

```json
{
  "AUTH_PROVIDER": "cognito",
  "AWS_REGION": "ap-southeast-1",
  "COGNITO_USER_POOL_ID": "ap-southeast-1_XXXX",
  "COGNITO_APP_CLIENT_ID": "xxxx",
  "COGNITO_APP_CLIENT_SECRET": "xxxx",
  "COGNITO_AUTH_FLOW": "ADMIN_USER_PASSWORD_AUTH",
  "SECRET_KEY": "your-secret-key",
  "DATABASE_URL": "sqlite:///./food_management.db"
}
```

- or dotenv/plain text format:

```dotenv
AUTH_PROVIDER=cognito
AWS_REGION=ap-southeast-1
COGNITO_USER_POOL_ID=ap-southeast-1_XXXX
COGNITO_APP_CLIENT_ID=xxxx
COGNITO_APP_CLIENT_SECRET=xxxx
COGNITO_AUTH_FLOW=ADMIN_USER_PASSWORD_AUTH
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./food_management.db
```

## 2. Configure vars

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars
```

For CI/CD deployments, this repo now includes environment-specific files:

- `staging.tfvars` (used for deploys to `dev`)
- `production.tfvars` (used for deploys to `main`)

Update both files with your real AWS values before enabling deploy workflow.

## 3. Deploy

```bash
terraform init
terraform plan
terraform apply
```

Outputs include public IP and URLs.

## 4. Cleanup after demo

```bash
terraform destroy
```

## EC2 vs ECS for your case

For a short 20-minute school demo, **EC2 is simpler and cheaper**.

Use ECS only if you need:
- autoscaling
- production-grade rolling deployments
- managed task scheduling/HA

For your requirement (short-lived, low memory, zero-cost target), single EC2 is the best fit.
