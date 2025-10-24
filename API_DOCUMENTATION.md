# Zabbix API Documentation

The REST endpoints in the `zabbix_api` app power the maps dashboard and the fibre route builder. The code is grouped into:

- `reports.py` - read-only endpoints for hosts, problems, status and cache clearing.
- `inventory.py` - operations that write to the local inventory (devices, ports, fibres, KML imports).
- `diagnostics.py` - guarded utilities such as ping or telnet that respect the diagnostics flag.
- `lookup.py` - lightweight lookups used by autocomplete widgets and helper dialogs.

`views.py` now re-exports these functions only for backwards compatibility.

## Diagnostics flag

Diagnostic endpoints are available only when `ENABLE_DIAGNOSTIC_ENDPOINTS=true`. The guard first checks the `.env` managed by `env_manager` (via `ENV_FILE_PATH`); if the key is absent it falls back to Django settings. When the flag is disabled the endpoints return HTTP 403 without running external commands.

## Base URL

```
http://localhost:8000/zabbix_api/
```

## Summary of categories

| Category   | Endpoint                    | Description                              |
|------------|-----------------------------|------------------------------------------|
| Test       | `/test/`                    | Quick connectivity check                 |
| Hosts      | `/hosts/`                   | Host inventory                           |
| Hosts      | `/hosts/{id}/`              | Host details                             |
| Network    | `/hosts/network-info/`      | Network info for every host              |
| Network    | `/hosts/{id}/network-info/` | Network info for a specific host         |
| Status     | `/status/`                  | Overall status of the Zabbix instance    |
| Problems   | `/problems/critical/`       | Critical problems only                   |
| Monitoring | `/monitoring/overview/`     | Global monitoring overview               |

All routes listed below are prefixed with `/zabbix_api/`.

## Status

- **GET** `/status/` - General summary of the Zabbix environment.

## Hosts

- **GET** `/hosts/` - List hosts with basic metadata.
- **GET** `/hosts/{hostid}/` - Full details of the selected host.
- **GET** `/hosts/{hostid}/items/` - Items grouped by category.
- **GET** `/hosts/{hostid}/triggers/` - Triggers ordered by severity.
- **GET** `/hosts/{hostid}/graphs/` - Available graphs.
- **GET** `/hosts/{hostid}/latest/` - Latest values for key items.
- **GET** `/hosts/{hostid}/performance/` - Performance metrics (CPU, memory, disk).
- **GET** `/items/{hostid}/{itemid}/history/` - Item history (24h by default).
- **GET** `/hosts/{hostid}/problems/` - Active problems affecting the host.

## Aggregated monitoring

- **GET** `/monitoring/overview/`
- **GET** `/monitoring/performance/`
- **GET** `/monitoring/availability/`
- **GET** `/monitoring/latest_all/`

Each endpoint returns summaries ready for dashboard cards and tables.

## Problems and events

- **GET** `/problems/` - All active problems.
- **GET** `/problems/summary/` - Aggregated view by severity.
- **GET** `/problems/by-severity/` - Count problems by severity level.
- **GET** `/problems/critical/` - Only critical incidents.
- **GET** `/events/` - Recent events.
- **GET** `/events/recent/` - Condensed chronological feed.
- **GET** `/events/summary/` - Distribution by severity/status.

## Network information

- **GET** `/hosts/network-info/`
- **GET** `/hosts/{hostid}/network-info/`

These endpoints provide interfaces, IP addresses and inventory metadata (latitude, longitude, address, and so on).

## Local inventory integration

Endpoints implemented in `inventory.py`:

- **POST** `/api/add-device-from-zabbix/`
- **POST** `/api/bulk-create-inventory/`
- **GET** `/api/device-ports/{device_id}/`
- **GET** `/api/device-ports-optical/{device_id}/`
- **GET** `/api/port-optical-status/{port_id}/`
- **GET** `/api/port-traffic-history/{port_id}/`
- **POST** `/api/import-fiber-kml/`
- **GET** `/api/fiber/live-status/{cable_id}/` (and related `fiber` / `fibers` variants)
- **GET** `/api/fiber/value-mapping-status/{cable_id}/`

All routes require authentication, and several reuse the diagnostics guard to prevent unsafe actions when the flag is disabled.

## Diagnostic tools

Implemented in `diagnostics.py`:

- **GET** `/api/test/ping/`
- **GET** `/api/test/telnet/`
- **GET** `/api/test/ping_telnet/`
- **POST** `/api/test/cable-up/{id}/` (plus the `cable-down` and `cable-unknown` helpers)

They require an authenticated staff user and `ENABLE_DIAGNOSTIC_ENDPOINTS=true`.

## Lookup endpoints

Implemented in `lookup.py`:

- **GET** `/lookup/hosts/`
- **GET** `/lookup/hosts/{hostid}/interfaces/`
- **GET** `/lookup/interfaces/{interfaceid}/details/`

These endpoints return lightweight payloads for autocomplete widgets and integration screens.
