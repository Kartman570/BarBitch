#!/usr/bin/env bash
# start.sh — fresh build & seed for BarPOS
# Usage:
#   ./start.sh                        # prompts for admin password
#   ./start.sh --admin-password=beer  # non-interactive

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}▸ $*${RESET}"; }
success() { echo -e "${GREEN}✔ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }
die()     { echo -e "${RED}✖ $*${RESET}" >&2; exit 1; }
header()  { echo -e "\n${BOLD}$*${RESET}"; }

# ── Admin password ────────────────────────────────────────────────────────────
ADMIN_PASSWORD=""
for arg in "$@"; do
  case "$arg" in
    --admin-password=*) ADMIN_PASSWORD="${arg#*=}" ;;
    *) die "Unknown argument: $arg" ;;
  esac
done
if [[ -z "$ADMIN_PASSWORD" ]]; then
  echo -ne "${BOLD}Admin password for the 'admin' account: ${RESET}"
  read -rs ADMIN_PASSWORD
  echo
fi
[[ -z "$ADMIN_PASSWORD" ]] && die "Admin password cannot be empty."

# ── .env setup ────────────────────────────────────────────────────────────────
header "── Environment"
ENV_FILE="$(dirname "$0")/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  warn ".env not found — creating from .env.example"
  [[ ! -f "$(dirname "$0")/.env.example" ]] && die ".env.example missing"
  cp "$(dirname "$0")/.env.example" "$ENV_FILE"
  # Generate a random SECRET_KEY and write it in
  NEW_KEY=$(openssl rand -hex 32)
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s/^SECRET_KEY=.*/SECRET_KEY=${NEW_KEY}/" "$ENV_FILE"
  else
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=${NEW_KEY}/" "$ENV_FILE"
  fi
  success ".env created with generated SECRET_KEY"
else
  # Ensure SECRET_KEY is set
  if grep -q '^SECRET_KEY=$' "$ENV_FILE"; then
    NEW_KEY=$(openssl rand -hex 32)
    if [[ "$(uname)" == "Darwin" ]]; then
      sed -i '' "s/^SECRET_KEY=$/SECRET_KEY=${NEW_KEY}/" "$ENV_FILE"
    else
      sed -i "s/^SECRET_KEY=$/SECRET_KEY=${NEW_KEY}/" "$ENV_FILE"
    fi
    warn "SECRET_KEY was empty — generated a new one"
  fi
  success ".env OK"
fi

cd "$(dirname "$0")"

# ── Tear down ─────────────────────────────────────────────────────────────────
header "── Tear down"
info "Stopping containers and wiping volumes..."
docker compose down -v --remove-orphans 2>/dev/null || true
success "Clean slate"

# ── Build ─────────────────────────────────────────────────────────────────────
header "── Build"
info "Building images (this may take a while on first run)..."
docker compose build
success "Build complete"

# ── Start services ────────────────────────────────────────────────────────────
header "── Start"
info "Starting db, app, client..."
docker compose up -d db app client
success "Containers started"

# ── Wait for Postgres ─────────────────────────────────────────────────────────
header "── Database"
info "Waiting for Postgres to accept connections..."
TRIES=0
until docker compose exec -T db pg_isready -U postgres -q 2>/dev/null; do
  TRIES=$((TRIES + 1))
  [[ $TRIES -ge 30 ]] && die "Postgres did not become ready in time."
  sleep 1
done
success "Postgres ready"

# ── Wait for the app API ──────────────────────────────────────────────────────
header "── Backend"
info "Waiting for FastAPI to be reachable..."
TRIES=0
until curl -sf http://localhost:8000/api/v1/auth/login -o /dev/null --max-time 2 -X POST \
      -H "Content-Type: application/json" -d '{}' 2>/dev/null; do
  # A 422 (validation error) also means the server is up
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 -X POST \
           http://localhost:8000/api/v1/auth/login \
           -H "Content-Type: application/json" -d '{}' 2>/dev/null || echo 0)
  [[ "$STATUS" != "0" ]] && break
  TRIES=$((TRIES + 1))
  [[ $TRIES -ge 60 ]] && die "Backend did not become ready in time."
  sleep 1
done
success "Backend ready"

# ── Migrations ────────────────────────────────────────────────────────────────
header "── Migrations"
info "Running alembic upgrade head..."
docker compose exec -T app alembic upgrade head
success "Schema up to date"

# ── Seed ─────────────────────────────────────────────────────────────────────
header "── Seed"
info "Creating roles, admin user, and sample menu items..."
docker compose exec -T app python -m cli seed-all --admin-password "$ADMIN_PASSWORD"
success "Database seeded"

# ── Tests ─────────────────────────────────────────────────────────────────────
header "── Tests"
info "Running test suite (isolated SQLite, does not touch the live DB)..."
if docker compose exec -T app python -m pytest tests/ --tb=short -q; then
  success "All tests passed"
else
  die "Tests failed — fix the issues above before using the app."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
header "── Ready"
echo -e "${GREEN}${BOLD}BarPOS is running!${RESET}"
echo ""
echo -e "  ${BOLD}Frontend${RESET}   http://localhost:8501"
echo -e "  ${BOLD}API${RESET}        http://localhost:8000"
echo -e "  ${BOLD}API docs${RESET}   http://localhost:8000/docs"
echo ""
echo -e "  Login: ${BOLD}admin${RESET} / ${BOLD}${ADMIN_PASSWORD}${RESET}"
echo ""
echo -e "  Stop:  ${CYAN}docker compose down${RESET}"
echo -e "  Logs:  ${CYAN}docker compose logs -f${RESET}"
