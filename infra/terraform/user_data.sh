#!/bin/bash
set -euo pipefail

apt-get update -y
apt-get install -y docker.io docker-compose-plugin git jq awscli
systemctl enable docker
systemctl start docker

usermod -aG docker ubuntu || true

mkdir -p /opt/fridgebuddy
if [ ! -d /opt/fridgebuddy/.git ]; then
  git clone --branch "${repo_branch}" "${repo_url}" /opt/fridgebuddy
else
  cd /opt/fridgebuddy
  git fetch origin
  git checkout "${repo_branch}"
  git pull origin "${repo_branch}"
fi

cd /opt/fridgebuddy

SECRET_STRING=$(aws secretsmanager get-secret-value \
  --region "${aws_region}" \
  --secret-id "${secrets_manager_arn}" \
  --query SecretString \
  --output text)

if echo "$SECRET_STRING" | jq -e . >/dev/null 2>&1; then
  echo "$SECRET_STRING" | jq -r 'to_entries[] | "\(.key)=\(.value)"' > .env
else
  echo "$SECRET_STRING" > .env
fi

# For demo stability, this keeps containers running across reboots.
docker compose up -d --build
