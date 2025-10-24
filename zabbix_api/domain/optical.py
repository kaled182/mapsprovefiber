from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from ..models import Port
from ..services.fiber_status import fetch_interface_status_advanced
from ..services.zabbix_service import zabbix_request

logger = logging.getLogger(__name__)

__all__ = [
    "_safe_float",
    "_fetch_item_value",
    "_score_optical_candidate",
    "_discover_optical_keys_by_portname",
    "_fetch_port_optical_snapshot",
]


def _safe_float(value: Any) -> Optional[float]:
    """Converte um valor potencialmente inválido para float, retornando None em caso de erro."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fetch_item_value(hostid: Any, key: str | None) -> Tuple[Optional[float], Optional[Any], Optional[Dict[str, Any]]]:
    """Retorna (valor_float, raw, item_dict) para um item do Zabbix."""
    if not (hostid and key):
        return None, None, None

    params: Dict[str, Any] = {
        "output": ["itemid", "lastvalue", "value_type", "units"],
        "hostids": [str(hostid)],
        "filter": {"key_": key},
        "limit": 1,
    }
    items = zabbix_request("item.get", params) or []
    if not items:
        params.pop("hostids", None)
        items = zabbix_request("item.get", params) or []
        if not items:
            return None, None, None

    item = items[0]
    raw = item.get("lastvalue")
    value = _safe_float(raw)
    if value is None:
        try:
            history = zabbix_request(
                "history.get",
                {
                    "itemids": [str(item["itemid"])],
                    "history": int(item.get("value_type", 0)),
                    "sortfield": "clock",
                    "sortorder": "DESC",
                    "limit": 1,
                },
            ) or []
        except Exception:  # pragma: no cover - fallback defensivo
            history = []
        if history:
            raw = history[0].get("value")
            value = _safe_float(raw)
    return value, raw, item


def _score_optical_candidate(item: Dict[str, Any], kind: str) -> int:
    """Aplica heurística simples para classificar itens RX/TX de potência óptica."""
    text = f"{(item.get('key_') or '').lower()} {(item.get('name') or '').lower()}"
    units = (item.get("units") or "").lower()
    score = 0

    if "power" in text:
        score += 2
    if "optical" in text or "fiber" in text:
        score += 1
    if "dbm" in text or "dbm" in units:
        score += 3

    if kind == "rx":
        if any(token in text for token in ("rx", "receive", "input")):
            score += 2
        if "tx" in text:
            score -= 1
    else:
        if any(token in text for token in ("tx", "transmit", "output")):
            score += 2
        if "rx" in text:
            score -= 1

    if any(word in text for word in ("threshold", "alarm", "bias", "temperature", "fault")):
        score -= 3
    return score


def _discover_optical_keys_by_portname(
    hostid: Any, port_name: str | None, cache: Optional[Dict[Tuple[str, str], Dict[str, Optional[str]]]] = None
) -> Dict[str, Optional[str]]:
    """
    Procura itens de potência óptica usando o nome da porta (fallback quando interfaceid não está disponível).
    Retorna dict {'rx': key_or_none, 'tx': key_or_none}.
    """
    cache_key = (str(hostid), port_name)
    if cache is not None and cache_key in cache:
        return cache[cache_key]

    if not (hostid and port_name):
        result = {"rx": None, "tx": None}
        if cache is not None:
            cache[cache_key] = result
        return result

    search_terms = [port_name]
    for sep in ("/", " ", ":"):
        if sep in port_name:
            compact = port_name.replace(sep, "")
            if compact and compact not in search_terms:
                search_terms.append(compact)

    candidates = []
    for term in search_terms:
        query = {
            "output": ["itemid", "key_", "name", "lastvalue", "units"],
            "hostids": [str(hostid)],
            "filter": {"status": "0"},
            "search": {"key_": term},
            "searchByAny": True,
            "limit": 200,
        }
        items = zabbix_request("item.get", query) or []
        candidates.extend(items)
        if items:
            break

    if not candidates:
        for term in search_terms:
            query = {
                "output": ["itemid", "key_", "name", "lastvalue", "units"],
                "hostids": [str(hostid)],
                "filter": {"status": "0"},
                "search": {"name": term},
                "searchByAny": True,
                "limit": 200,
            }
            items = zabbix_request("item.get", query) or []
            candidates.extend(items)
            if items:
                break

    rx_key = tx_key = None
    best_rx = best_tx = -999

    for item in candidates:
        key = item.get("key_")
        if not key:
            continue
        rx_score = _score_optical_candidate(item, "rx")
        tx_score = _score_optical_candidate(item, "tx")
        if rx_score > best_rx:
            best_rx = rx_score
            rx_key = key if rx_score > 0 else rx_key
        if tx_score > best_tx:
            best_tx = tx_score
            tx_key = key if tx_score > 0 else tx_key

    result = {"rx": rx_key, "tx": tx_key}
    if cache is not None:
        cache[cache_key] = result
    return result


def _fetch_port_optical_snapshot(
    port: Port | None, discovery_cache: Optional[Dict[Tuple[str, str], Dict[str, Optional[str]]]] = None, persist_keys: bool = True
) -> Dict[str, Any]:
    """
    Obtém snapshot de potência óptica (RX/TX) para uma porta.
    - Usa chaves configuradas no modelo, com fallback para descoberta automática.
    - Persiste chaves descobertas (se `persist_keys` for True).
    Retorna dict com valores numéricos (dBm) e metadados.
    """
    if port is None or port.device is None:
        return {"rx_dbm": None, "tx_dbm": None, "rx_raw": None, "tx_raw": None}

    hostid = (port.device.zabbix_hostid or "").strip()
    if not hostid:
        return {"rx_dbm": None, "tx_dbm": None, "rx_raw": None, "tx_raw": None}

    discovery_cache = discovery_cache if discovery_cache is not None else {}
    rx_key = (port.rx_power_item_key or "").strip()
    tx_key = (port.tx_power_item_key or "").strip()
    interfaceid = (port.zabbix_interfaceid or "").strip()

    status_meta: Dict[str, Any] = {}
    try:
        _, status_meta = fetch_interface_status_advanced(
            hostid,
            primary_item_key=(port.zabbix_item_key or "").strip() or None,
            interfaceid=interfaceid or None,
            rx_key=rx_key or None,
            tx_key=tx_key or None,
        )
    except Exception as exc:  # pragma: no cover - log defensivo
        logger.debug("Erro ao consultar status óptico da porta %s: %s", port.id, exc)
        status_meta = {}

    original_rx_key = rx_key
    original_tx_key = tx_key

    for meta_key in ("rx_key", "rx_key_generic"):
        candidate = status_meta.get(meta_key)
        if candidate:
            rx_key = candidate.strip()
            break
    for meta_key in ("tx_key", "tx_key_generic"):
        candidate = status_meta.get(meta_key)
        if candidate:
            tx_key = candidate.strip()
            break

    if (not rx_key or not tx_key) and port.name:
        discovered = _discover_optical_keys_by_portname(hostid, port.name, cache=discovery_cache)
        rx_key = rx_key or (discovered.get("rx") or "")
        tx_key = tx_key or (discovered.get("tx") or "")
        if discovered.get("rx") or discovered.get("tx"):
            status_meta.setdefault("auto_discovery", "port_name")

    updates: Dict[str, Any] = {}
    if rx_key and rx_key != original_rx_key:
        updates["rx_power_item_key"] = rx_key
    if tx_key and tx_key != original_tx_key:
        updates["tx_power_item_key"] = tx_key

    if persist_keys and updates:
        Port.objects.filter(pk=port.pk).update(**updates)
        for field, value in updates.items():
            setattr(port, field, value)

    rx_value = rx_raw = None
    tx_value = tx_raw = None
    if rx_key:
        rx_value, rx_raw, _ = _fetch_item_value(hostid, rx_key)
    if tx_key:
        tx_value, tx_raw, _ = _fetch_item_value(hostid, tx_key)

    result: Dict[str, Any] = {
        "rx_dbm": rx_value,
        "tx_dbm": tx_value,
        "rx_raw": rx_raw,
        "tx_raw": tx_raw,
        "rx_key": rx_key or None,
        "tx_key": tx_key or None,
    }
    if status_meta:
        result["meta"] = status_meta
    if updates:
        result["keys_updated"] = True
    return result

