#!/usr/bin/env bash
set -Eeuo pipefail

SERVICE_NAME="${SERVICE_NAME:-speedtest-vps-api}"
APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-6969}"
SERVICE_USER="${SERVICE_USER:-root}"
SERVICE_GROUP="${SERVICE_GROUP:-}"
INSTALL_SPEEDTEST_CLI="${INSTALL_SPEEDTEST_CLI:-1}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/.venv}"
STATE_DIR="${STATE_DIR:-/var/lib/$SERVICE_NAME}"
DATABASE_PATH="${SPEEDTEST_DB_PATH:-$STATE_DIR/speedtest_results.sqlite3}"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

fail() {
  echo "Erro: $*" >&2
  exit 1
}

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    fail "execute com sudo: sudo $0"
  fi
}

validate_environment() {
  [[ "$APP_PORT" =~ ^[0-9]+$ ]] || fail "APP_PORT deve ser um numero inteiro."
  [[ "$APP_PORT" -ge 1 && "$APP_PORT" -le 65535 ]] || fail "APP_PORT deve estar entre 1 e 65535."

  command -v apt-get >/dev/null 2>&1 || fail "apt-get nao encontrado. Este script foi feito para Ubuntu/Debian."
  command -v systemctl >/dev/null 2>&1 || fail "systemctl nao encontrado."

  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    if [[ "${ID:-}" != "ubuntu" ]]; then
      echo "Aviso: sistema detectado: ${PRETTY_NAME:-desconhecido}. O script foi feito para Ubuntu."
    fi
  fi
}

install_system_packages() {
  export DEBIAN_FRONTEND=noninteractive

  apt-get update
  apt-get install -y \
    ca-certificates \
    curl \
    python3 \
    python3-pip \
    python3-venv
}

install_speedtest_cli() {
  if command -v speedtest >/dev/null 2>&1; then
    echo "Ookla Speedtest CLI ja esta instalado: $(command -v speedtest)"
    return
  fi

  if [[ "$INSTALL_SPEEDTEST_CLI" != "1" ]]; then
    echo "Aviso: INSTALL_SPEEDTEST_CLI=0. Pulando instalacao do Ookla Speedtest CLI."
    echo "       A API sobe, mas /speedtest retornara 503 ate o binario 'speedtest' existir no PATH."
    return
  fi

  echo "Instalando Ookla Speedtest CLI..."
  curl -fsSL https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash
  apt-get update
  apt-get install -y speedtest
}

install_python_dependencies() {
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
  "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
}

write_systemd_service() {
  if [[ "$SERVICE_USER" != "root" ]] && ! id "$SERVICE_USER" >/dev/null 2>&1; then
    fail "usuario SERVICE_USER='$SERVICE_USER' nao existe."
  fi

  if [[ -z "$SERVICE_GROUP" ]]; then
    SERVICE_GROUP="$(id -gn "$SERVICE_USER")"
  fi

  mkdir -p "$(dirname "$DATABASE_PATH")"
  touch "$DATABASE_PATH"
  if [[ "$SERVICE_USER" != "root" ]]; then
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$VENV_DIR" "$(dirname "$DATABASE_PATH")"
  fi

  cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=Speedtest VPS API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1
Environment=SPEEDTEST_DB_PATH=$DATABASE_PATH
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$VENV_DIR/bin/uvicorn app.main:app --host $APP_HOST --port $APP_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
}

enable_service() {
  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
  systemctl restart "$SERVICE_NAME"
}

print_summary() {
  echo
  echo "Deploy concluido."
  echo "Servico: $SERVICE_NAME"
  echo "Porta: $APP_PORT"
  echo "Banco SQLite: $DATABASE_PATH"
  echo "URL local: http://127.0.0.1:$APP_PORT"
  echo "Health check: curl http://127.0.0.1:$APP_PORT/health"
  echo
  echo "Comandos uteis:"
  echo "  systemctl status $SERVICE_NAME"
  echo "  journalctl -u $SERVICE_NAME -f"
}

require_root
validate_environment
install_system_packages
install_speedtest_cli
install_python_dependencies
write_systemd_service
enable_service
print_summary
