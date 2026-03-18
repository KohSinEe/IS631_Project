#!/bin/bash
set -euo pipefail

LOG_FILE="/var/log/fridgebuddy-user-data.log"
exec > >(tee -a "$LOG_FILE") 2>&1

log() {
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*"
}

die() {
  log "ERROR: $*"
  exit 1
}

retry() {
  local attempts="$1"
  shift
  local n=1
  until "$@"; do
    if [ "$n" -ge "$attempts" ]; then
      return 1
    fi
    n=$((n + 1))
    sleep 3
  done
}

check_required_vars() {
  [ -n "${aws_region}" ] || die "aws_region is empty"
  [ -n "${repo_url}" ] || die "repo_url is empty"
  [ -n "${repo_branch}" ] || die "repo_branch is empty"
  [ -n "${secrets_manager_arn}" ] || die "secrets_manager_arn is empty"
}

wait_for_http() {
  local url="$1"
  local name="$2"
  local attempts="$${3:-30}"
  local delay="$${4:-5}"

  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "$name is reachable at $url"
      return 0
    fi
    sleep "$delay"
  done

  return 1
}

trap 'die "user_data failed at line $LINENO"' ERR

log "Starting FridgeBuddy EC2 bootstrap"
check_required_vars

retry 5 apt-get update -y
retry 5 apt-get install -y docker.io docker-compose-plugin git jq awscli curl

systemctl enable docker
systemctl start docker
systemctl is-active --quiet docker || die "Docker service is not active"

usermod -aG docker ubuntu || true

mkdir -p /opt/fridgebuddy
if [ ! -d /opt/fridgebuddy/.git ]; then
  log "Cloning repository ${repo_url} (${repo_branch})"
  retry 3 git clone --branch "${repo_branch}" "${repo_url}" /opt/fridgebuddy
else
  log "Updating existing repository checkout"
  cd /opt/fridgebuddy
  retry 3 git fetch origin
  git checkout "${repo_branch}"
  retry 3 git pull origin "${repo_branch}"
fi

cd /opt/fridgebuddy

log "Fetching environment secret from Secrets Manager"
SECRET_STRING=$(aws secretsmanager get-secret-value \
  --region "${aws_region}" \
  --secret-id "${secrets_manager_arn}" \
  --query SecretString \
  --output text)

[ -n "$SECRET_STRING" ] || die "SecretString is empty"
[ "$SECRET_STRING" != "None" ] || die "SecretString returned None"

if echo "$SECRET_STRING" | jq -e . >/dev/null 2>&1; then
  echo "$SECRET_STRING" | jq -r 'to_entries[] | "\(.key)=\(.value)"' > .env
else
  echo "$SECRET_STRING" > .env
fi

[ -s .env ] || die ".env file is missing or empty"

log "Validating docker compose configuration"
docker compose config --quiet

log "Starting containers"
docker compose up -d --build
docker compose ps

wait_for_http "http://127.0.0.1:8000/docs" "FastAPI" 36 5 || {
  docker compose logs api --tail 200 || true
  die "FastAPI failed readiness check"
}

wait_for_http "http://127.0.0.1:8501" "Streamlit" 48 5 || {
  docker compose logs frontend --tail 200 || true
  die "Streamlit failed readiness check"
}

log "FridgeBuddy bootstrap completed successfully"
