# Speedtest VPS API

API FastAPI para medir a velocidade de conexao do servidor usando o Ookla Speedtest CLI.

## Requisitos

- Python 3.10+
- Ookla Speedtest CLI instalado e disponivel no `PATH` como `speedtest`

## Instalar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
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
