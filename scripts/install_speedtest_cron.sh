#!/usr/bin/env bash
set -Eeuo pipefail

MARKER="# speedtest-vps-api-cron"
DEFAULT_SCHEDULE="0 * * * *"
DEFAULT_LOG_FILE="/var/log/cron_api.log"
DEFAULT_MAX_TIME="180"

usage() {
  cat <<'EOF'
Uso:
  scripts/install_speedtest_cron.sh "https://sua-api.com/speedtest"

Variaveis opcionais:
  SCHEDULE="0 * * * *"              Agenda cron. Padrao: a cada hora.
  LOG_FILE="/var/log/cron_api.log"  Arquivo de log.
  MAX_TIME="180"                    Timeout do curl em segundos.

Exemplos:
  scripts/install_speedtest_cron.sh "http://localhost:8000/speedtest"

  SCHEDULE="*/30 * * * *" \
  LOG_FILE="$HOME/speedtest-cron.log" \
  MAX_TIME="240" \
  scripts/install_speedtest_cron.sh "https://sua-api.com/speedtest?timeout=180"
EOF
}

fail() {
  echo "Erro: $*" >&2
  exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

SPEEDTEST_URL="${1:-${SPEEDTEST_URL:-}}"
SCHEDULE="${SCHEDULE:-$DEFAULT_SCHEDULE}"
LOG_FILE="${LOG_FILE:-$DEFAULT_LOG_FILE}"
MAX_TIME="${MAX_TIME:-$DEFAULT_MAX_TIME}"

[[ -n "$SPEEDTEST_URL" ]] || {
  usage
  fail "informe a URL da rota /speedtest."
}

[[ "$SPEEDTEST_URL" =~ ^https?:// ]] || fail "a URL deve comecar com http:// ou https://."
[[ "$MAX_TIME" =~ ^[0-9]+$ ]] || fail "MAX_TIME deve ser um numero inteiro."

command -v curl >/dev/null 2>&1 || fail "curl nao encontrado. Instale com: sudo apt-get install -y curl"
command -v crontab >/dev/null 2>&1 || fail "crontab nao encontrado. Instale com: sudo apt-get install -y cron"

if command -v systemctl >/dev/null 2>&1; then
  if ! systemctl is-active --quiet cron; then
    echo "Aviso: o servico cron nao esta ativo. No Ubuntu, habilite com:"
    echo "  sudo systemctl enable --now cron"
  fi
fi

log_dir="$(dirname "$LOG_FILE")"
mkdir -p "$log_dir" 2>/dev/null || true
touch "$LOG_FILE" 2>/dev/null || {
  echo "Aviso: nao foi possivel criar '$LOG_FILE' com o usuario atual."
  echo "       Execute com sudo ou defina LOG_FILE para um caminho gravavel."
}

cron_command="/usr/bin/curl --fail --silent --show-error --max-time $MAX_TIME \"$SPEEDTEST_URL\" >> \"$LOG_FILE\" 2>&1"
cron_line="$SCHEDULE $cron_command $MARKER"

current_crontab="$(mktemp)"
new_crontab="$(mktemp)"
trap 'rm -f "$current_crontab" "$new_crontab"' EXIT

crontab -l >"$current_crontab" 2>/dev/null || true
grep -vF "$MARKER" "$current_crontab" >"$new_crontab" || true
printf '%s\n' "$cron_line" >>"$new_crontab"
crontab "$new_crontab"

echo "Cron instalado com sucesso:"
echo "$cron_line"
