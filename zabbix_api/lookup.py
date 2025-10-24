from __future__ import annotations

import re

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .decorators import handle_api_errors
from .services.zabbix_service import (
    fetch_host_availability,
    get_host_interfaces,
    get_interface_snmp_details,
    search_hosts,
    search_hosts_by_name_ip,
)


def _parse_groupids(raw: str | None) -> list[str]:
    if not raw:
        return []
    tokens = re.split(r"[\s,;]+", str(raw))
    result: list[str] = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        try:
            int(token)
        except ValueError:
            continue
        result.append(token)
    return result


def _parse_limit(raw: str | None, *, default: int, max_v: int) -> int:
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    if value > max_v:
        return max_v
    return value


@require_GET
@handle_api_errors
def lookup_hosts(request):
    """
    GET /zabbix_api/lookup/hosts?q=<texto>&groupids=1,2&limit=20
    Busca hosts no Zabbix para autocomplete (nome/IP), com cache curto.
    """
    q = (request.GET.get("q") or "").strip()
    groupids = _parse_groupids(request.GET.get("groupids", ""))
    limit = _parse_limit(request.GET.get("limit", "20"), default=20, max_v=200)

    if not q and not groupids:
        return JsonResponse(
            {"success": False, "error": "Par?metro 'q' ou 'groupids' ? obrigat?rio."},
            status=400,
        )

    data = (
        search_hosts_by_name_ip(q, groupids=groupids, limit=limit)
        if q
        else search_hosts(query=q, groupids=groupids, limit=limit)
    ) or []

    return JsonResponse({"success": True, "data": data, "count": len(data)})


@require_GET
@handle_api_errors
def lookup_host_interfaces(request, hostid):
    """
    GET /zabbix_api/lookup/hosts/<hostid>/interfaces?only_main=true&limit=200
    Lista interfaces (hostinterface.get) de um host espec?fico.
    """
    if not hostid:
        return JsonResponse(
            {"success": False, "error": "Par?metro 'hostid' ? obrigat?rio."},
            status=400,
        )

    only_main = (request.GET.get("only_main", "false") or "").lower() == "true"
    limit = _parse_limit(request.GET.get("limit", "200"), default=200, max_v=500)

    interfaces = get_host_interfaces(hostid, only_main=only_main, limit=limit) or []
    return JsonResponse({"success": True, "data": interfaces, "count": len(interfaces)})


@require_GET
@handle_api_errors
def lookup_host_status(request, hostid):
    """
    GET /zabbix_api/lookup/hosts/<hostid>/status/
    Retorna disponibilidade agregada do host (canal + interfaces).
    """
    payload = fetch_host_availability(hostid)
    return JsonResponse({"success": True, "data": payload})


@require_GET
@handle_api_errors
def lookup_interface_details(request, interfaceid):
    """
    GET /zabbix_api/lookup/interfaces/<interfaceid>/details
    Detalhes de uma interface Zabbix (hostinterface) + dados SNMP se dispon?veis.
    """
    details = get_interface_snmp_details(str(interfaceid))
    if not details:
        return JsonResponse(
            {"success": False, "error": "Interface n?o encontrada."}, status=404
        )
    return JsonResponse({"success": True, "data": details})
