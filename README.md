# Django Maps â€“ Operations & Deployment Guide

This project collects Zabbix telemetry and renders it in two web experiences:

* **Maps Dashboard (`/maps_view/dashboard/`)** â€“ status cards, host availability and shortcuts to diagnostics.
* **Fiber Route Builder (`/routes_builder/fiber-route-builder/`)** â€“ draw or import fibre routes (KML), monitor optical power and manage cable metadata.

Observability is built in through Prometheus metrics, structured logging and slow-query inspection. Secrets stay outside the repository and are managed via the bundled setup panel.

---

## 1. Requirements

| Component | Version / Notes |
|-----------|-----------------|
| Python    | 3.12+ (tested with 3.12) |
| Node.js   | 18+ (for the existing frontend toolchain) |
| MariaDB / MySQL | Used as primary database (`mapspro_db`). Slow-query log is optional but recommended. |
| Redis     | Acts as Celery broker/result backend (`redis://127.0.0.1:6379/0` by default). |
| Celery worker | Required for async tasks such as warming optical snapshots. |
| Prometheus (optional) | Scrapes `/metrics/` endpoint for dashboards/alerts. |

### Python dependencies

All server-side dependencies are pinned in `requirements.txt`. Install them in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate         # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 2. Environment configuration

The project relies on Django settings + environment variables managed through [`django-environ`](https://github.com/joke2k/django-environ).

1. Copy `.env.example` to `.env` and fill the placeholders (database credentials, Redis URL, API keys, etc.).
2. Generate or reuse a `FERNET_KEY` â€“ it encrypts sensitive values stored through the setup panel:

   ```bash
   python manage.py generate_fernet_key --write
   ```

3. When running in production, prefer exporting real environment variables or set `ENV_FILE_PATH` to the secure location of your `.env`.

Key flags:

* `ENABLE_DIAGNOSTIC_ENDPOINTS` â€” required for ping/telnet utilities and optical diagnostics.
* `ENABLE_DIAGNOSTIC_ENDPOINTS=true` should only be set for trusted environments.
* `CHANNEL_LAYER_URL` â€” optional Channels backend (e.g. `redis://127.0.0.1:6379/1`). Omit for the in-memory layer used in development.

---

## 3. First run

1. Apply migrations and collect static assets:

   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

2. Create an admin user `python manage.py createsuperuser`.
3. Start supporting services: MariaDB, Redis, a Celery worker and Celery beat (for realtime broadcasts).

   ```bash
   # Terminal 1 â€“ Django/Channels (development)
   python manage.py runserver 0.0.0.0:8000

   # or, for ASGI servers in staging/production
   daphne -b 0.0.0.0 -p 8000 core.asgi:application

   # Terminal 2 â€“ Celery worker
   celery -A core worker -l info
   # Windows tip: add `--pool=solo` if you see spawn/prefork errors

   # Terminal 3 â€“ Celery beat (required for realtime dashboard)
   celery -A core beat -l info
   # Windows tip: you can also append `--pool=solo`
   ```

4. Open `/setup_app/first_time/` to feed company and Zabbix credentials. The panel writes the `.env` (when allowed) and caches runtime settings (`setup_app.services.runtime_settings`).

5. After authentication, Quick Actions â†’ **Configure System** (`/setup_app/config/`) lets you rotate credentials and feature flags.

---

## 4. Daily operations

### Fibre Route Builder

* Draw paths manually and save; a modal collects origin/destination devices + ports.
* Import KML (single line-string) via the **Import KML** button. The modal now mirrors the manual save modal and allows one-way monitoring (single-port).
* Every import/save fires a UI refresh â€“ the dropdown is cleared so you can explicitly load the cable you need.

### Metrics & Logging

* `/metrics/` exposes Prometheus metrics (Django, MariaDB, Redis, Celery). A friendly HTML explorer lives at `/maps_view/metrics/`.
* Structured logging lands in `logs/application.log` (rotating 5 MB files). Console output is also enabled.
* Slow query log analysis: `python manage.py show_slow_queries --path "/var/lib/mysql/hostname-slow.log" --limit 10`. It also honours `MYSQL_SLOW_LOG_PATH`.
* Celery beat keeps the realtime dashboard in sync - leave `celery -A core beat -l info` running alongside the worker.

### Realtime dashboard

* The WebSocket endpoint `/ws/dashboard/status/` streams host availability snapshots via Django Channels.
* Configure `CHANNEL_LAYER_URL` to point at your Redis instance in multi-process environments; the default in-memory layer is suitable only for development.
* When the WebSocket is unavailable the dashboard banner indicates the offline state and the UI falls back to periodic HTTP refreshes.

### Observability checklist

See `docs/performance_phase6.md` for detailed steps. Highlights:

* Hook `/metrics/` to Prometheus/Grafana.
* Automate slow-log ingestion (command above).
* Consider APM integration for HTTP/Celery traces.

---

## 5. Diagnostics & APIs

The `zabbix_api` app is split into focused modules:

| Module | Responsibility |
|--------|----------------|
| `reports.py` | Read-only Zabbix data (hosts, problems, cache clearing). |
| `inventory.py` | Device/port/cable CRUD, KML import, manual route save, optical insights. |
| `diagnostics.py` | Guarded utilities (ping, telnet, mocks). |
| `lookup.py` | Autocomplete helpers, host lookups, interface details. |

Public endpoints are re-exported in `zabbix_api/views.py` for backward compatibility.

---

## 6. Running tests

```bash
python manage.py test tests setup_app
```

The suite covers runtime settings, diagnostics guards, inventory API and smoke tests. Extend it for custom flows and regression coverage.

---

## 7. Deployment checklist

1. Copy `.env.example` to the target node and populate real values (or export env vars).
2. Set `DEBUG=False`, configure `ALLOWED_HOSTS` and your TLS/CSRF settings.
3. Run migrations + collect static files.
4. Start Django (Gunicorn/Uvicorn) behind your preferred web server.
5. Launch Celery worker(s) and beat (required for scheduled tasks and realtime broadcasts).
6. Point Prometheus or another collector to `/metrics/`.
7. Configure log rotation/ shipping (the app already handles rotation inside `logs/`).
8. Optionally configure backup automation (see below).

---

## 8. Backup & release packaging

The repository ships with a PowerShell helper that creates a sanitized ZIP (excludes virtualenvs, node modules, caches). Run from the project root:

```powershell
pwsh scripts\package-release.ps1
```

The script collects sources into `dist/django-maps-release-YYYYmmddHHMM.zip`. Distribute that bundle to testing or production servers, then install dependencies and run migrations as outlined above.

For manual backups you can run:

```powershell
Compress-Archive `
  -Path * `
  -DestinationPath dist\django-maps-backup.zip `
  -CompressionLevel Optimal `
  -Exclude *.pyc,*__pycache__*,.git*,.venv*,venv*,logs\*,node_modules\*
```

Remember to back up the database (`mysqldump`) and `.env`/`FERNET_KEY` separately.

---

## 9. Useful commands reference

| Command | Purpose |
|---------|---------|
| `python manage.py show_slow_queries --limit 10` | Inspect MariaDB/MySQL slow query log. |
| `python manage.py collectstatic` | Gather static assets for deployment. |
| `celery -A core worker -l info` | Start Celery worker. |
| `celery -A core beat -l info` | (Optional) Run scheduled tasks (warm optical snapshots). |
| `python manage.py shell_plus` (if installed) | Explore Django ORM interactively. |

---

## 10. Further reading

* `docs/performance_phase1..6.md` â€“ progressive hardening & observability improvements.
* `docs/operations_checklist.md` (new) â€“ concise runbook for dayâ€‘toâ€‘day ops.
* `API_DOCUMENTATION.md` â€“ legacy reference for REST endpoints.

This README acts as the entry point for onboarding, dayâ€‘toâ€‘day operation and deployment of the Django Maps platform. Contributions improving automation, monitoring or documentation are welcome. Continuous updates keep the bundle deployable and productionâ€‘ready.

---

## Refatoracao em andamento
- Casos de uso de fibras e inventario residem agora em zabbix_api/usecases para compartilhar regras entre views, tasks e comandos.
- O arquivo zabbix_api/inventory.py tornou-se uma camada fina de HTTP; detalhes de evolucao estao em docs/refactor_fibers.md.

## Executar testes rapidamente
`
python -m pytest tests
`

## Gerar pacote para validacao/implantacao
`
pwsh scripts/package-release.ps1
`
O script produz um ZIP em dist/ ignorando dependencias locais (env, 
ode_modules, oracleJdk-25, logs) e pode ser publicado para testes externos.
