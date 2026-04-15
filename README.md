# Speedtest VPS API

API FastAPI para medir a velocidade de conexao do servidor usando o Ookla Speedtest CLI.

## Requisitos

- Python 3.10+
- Ookla Speedtest CLI instalado e disponivel no `PATH` como `speedtest`

## Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Deploy no Ubuntu

O script de deploy cria o virtualenv, instala os `requirements.txt`, instala pacotes do sistema, configura o Ookla Speedtest CLI e cria um service no systemd rodando na porta `6969`.

```bash
chmod +x scripts/deploy_ubuntu.sh
sudo scripts/deploy_ubuntu.sh
```

Depois do deploy:

```bash
curl http://127.0.0.1:6969/health
systemctl status speedtest-vps-api
journalctl -u speedtest-vps-api -f
```

Variaveis opcionais:

```bash
SERVICE_NAME="speedtest-vps-api" \
APP_PORT="6969" \
SERVICE_USER="root" \
INSTALL_SPEEDTEST_CLI="1" \
sudo -E scripts/deploy_ubuntu.sh
```

Para pular a instalacao do Ookla Speedtest CLI:

```bash
INSTALL_SPEEDTEST_CLI=0 sudo -E scripts/deploy_ubuntu.sh
```

## Endpoints

### Health check

```bash
curl http://localhost:8000/health
```

Resposta:

```json
{
  "status": "ok"
}
```

### Verificar velocidade

```bash
curl http://localhost:8000/speedtest
```

Tambem e possivel ajustar o timeout:

```bash
curl "http://localhost:8000/speedtest?timeout=180"
```

Exemplo de resposta:

```json
{
  "id": 1,
  "created_at": "2026-04-15T16:30:00.000000Z",
  "download": {
    "bandwidth_bytes_per_second": 12500000,
    "bits_per_second": 100000000,
    "mbps": 100.0
  },
  "upload": {
    "bandwidth_bytes_per_second": 6250000,
    "bits_per_second": 50000000,
    "mbps": 50.0
  },
  "ping": {
    "latency_ms": 8.123,
    "jitter_ms": 0.52
  },
  "server": {
    "id": 1234,
    "name": "Example Server",
    "location": "Sao Paulo",
    "country": "Brazil",
    "host": "speedtest.example.net"
  },
  "isp": "Example ISP",
  "result_url": "https://www.speedtest.net/result/c/example"
}
```

O endpoint executa internamente:

```bash
speedtest --accept-license --accept-gdpr -f json
```

Cada medicao bem-sucedida e salva automaticamente no SQLite em `speedtest_results.sqlite3`.
Para usar outro caminho, defina a variavel de ambiente `SPEEDTEST_DB_PATH`.

### Historico para graficos

```bash
curl "http://localhost:8000/speedtest/history?limit=100"
```

Resposta:

```json
{
  "count": 2,
  "points": [
    {
      "id": 1,
      "created_at": "2026-04-15T16:30:00.000000Z",
      "download_mbps": 100.0,
      "upload_mbps": 50.0,
      "ping_latency_ms": 8.123,
      "ping_jitter_ms": 0.52,
      "isp": "Example ISP",
      "server_name": "Example Server",
      "server_location": "Sao Paulo",
      "server_country": "Brazil"
    },
    {
      "id": 2,
      "created_at": "2026-04-15T16:35:00.000000Z",
      "download_mbps": 98.4,
      "upload_mbps": 49.7,
      "ping_latency_ms": 8.4,
      "ping_jitter_ms": 0.61,
      "isp": "Example ISP",
      "server_name": "Example Server",
      "server_location": "Sao Paulo",
      "server_country": "Brazil"
    }
  ]
}
```

## Cron no Ubuntu

Use o script abaixo para instalar uma chamada periodica da rota `/speedtest` no crontab:

```bash
chmod +x scripts/install_speedtest_cron.sh
scripts/install_speedtest_cron.sh "http://localhost:8000/speedtest"
```

Por padrao, ele instala uma execucao a cada hora:

```cron
0 * * * * /usr/bin/curl --fail --silent --show-error --max-time 180 "http://localhost:8000/speedtest" >> "/var/log/cron_api.log" 2>&1 # speedtest-vps-api-cron
```

Configuracao com variaveis:

```bash
SCHEDULE="*/30 * * * *" \
LOG_FILE="$HOME/speedtest-cron.log" \
MAX_TIME="240" \
scripts/install_speedtest_cron.sh "https://sua-api.com/speedtest?timeout=180"
```

O script e idempotente: ao rodar novamente, ele substitui a entrada antiga marcada com `# speedtest-vps-api-cron` em vez de duplicar o cron.
