from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .decorators import handle_api_errors
from .services.zabbix_service import (
    clear_token_cache,
    format_host_data,
    get_host_performance_metrics,
    get_host_problems,
    zabbix_request,
)


def _json_error(message: str, status: int = 500) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


@require_GET
@handle_api_errors
def zabbix_hosts(request):
    params = {
        "output": ["hostid", "host", "name", "status", "available", "error"],
        "selectGroups": ["groupid", "name"],
        "selectInterfaces": ["interfaceid", "ip", "port", "type"],
    }
    result = zabbix_request("host.get", params) or []
    return JsonResponse({"total": len(result), "hosts": format_host_data(result)})


@require_GET
@handle_api_errors
def zabbix_host_detail(request, hostid: int):
    params = {
        "output": "extend",
        "hostids": hostid,
        "selectGroups": ["groupid", "name"],
        "selectInterfaces": "extend",
        "selectItems": ["itemid", "name", "key_", "status", "type"],
        "selectTriggers": ["triggerid", "description", "status", "priority"],
        "selectMacros": "extend",
    }
    result = zabbix_request("host.get", params) or []
    if not result:
        return _json_error("Host not found", 404)

    formatted = format_host_data(result)[0]
    formatted["items"] = result[0].get("items", [])
    formatted["triggers"] = result[0].get("triggers", [])
    formatted["macros"] = result[0].get("macros", [])
    formatted["last_update"] = datetime.now().isoformat()
    return JsonResponse(formatted)


@require_GET
@handle_api_errors
def zabbix_host_items(request, hostid: int):
    params = {
        "output": ["itemid", "name", "key_", "status", "type", "units", "delay"],
        "hostids": hostid,
        "filter": {"status": 0},
        "sortfield": "name",
    }
    items = zabbix_request("item.get", params) or []
    return JsonResponse({"hostid": hostid, "items": items, "count": len(items)})


@require_GET
@handle_api_errors
def zabbix_host_triggers(request, hostid: int):
    params = {
        "output": ["triggerid", "description", "status", "priority", "lastchange"],
        "hostids": hostid,
        "sortfield": "priority",
        "sortorder": "DESC",
    }
    data = zabbix_request("trigger.get", params) or []
    return JsonResponse({"hostid": hostid, "triggers": data, "count": len(data)})


@require_GET
@handle_api_errors
def zabbix_host_graphs(request, hostid: int):
    params = {
        "output": ["graphid", "name", "width", "height"],
        "hostids": hostid,
        "sortfield": "name",
    }
    data = zabbix_request("graph.get", params) or []
    return JsonResponse({"hostid": hostid, "graphs": data, "count": len(data)})


@require_GET
@handle_api_errors
def zabbix_host_latest_data(request, hostid: int):
    items = zabbix_request(
        "item.get",
        {
            "output": ["itemid", "name", "key_", "units", "value_type"],
            "hostids": hostid,
            "filter": {"status": 0},
            "limit": 50,
        },
    ) or []

    latest = []
    for item in items:
        history = zabbix_request(
            "history.get",
            {
                "itemids": item["itemid"],
                "history": item["value_type"],
                "sortfield": "clock",
                "sortorder": "DESC",
                "limit": 1,
            },
        ) or []
        latest_value = history[0] if history else None
        latest.append(
            {
                "itemid": item["itemid"],
                "name": item["name"],
                "key": item["key_"],
                "units": item.get("units", ""),
                "value": latest_value.get("value") if latest_value else None,
                "timestamp": latest_value.get("clock") if latest_value else None,
            }
        )

    return JsonResponse({"hostid": hostid, "items": latest})


@require_GET
@handle_api_errors
def zabbix_item_history(request, hostid: int, itemid: int):
    hours = int(request.GET.get("hours", "24"))
    time_from = int((datetime.now() - timedelta(hours=hours)).timestamp())
    item_info = zabbix_request(
        "item.get",
        {
            "output": ["name", "key_", "units", "value_type"],
            "itemids": itemid,
            "hostids": hostid,
        },
    ) or []
    if not item_info:
        return _json_error("Item not found", 404)

    history = zabbix_request(
        "history.get",
        {
            "itemids": itemid,
            "history": item_info[0]["value_type"],
            "time_from": time_from,
            "sortfield": "clock",
            "sortorder": "ASC",
        },
    ) or []

    payload = [
        {
            "timestamp": int(point["clock"]),
            "value": float(point["value"]) if point["value"].replace(".", "", 1).isdigit() else point["value"],
        }
        for point in history
    ]
    return JsonResponse({"hostid": hostid, "itemid": itemid, "history": payload})


@require_GET
@handle_api_errors
def zabbix_host_performance(request, hostid: int):
    metrics = get_host_performance_metrics(hostid)
    if metrics is None:
        return _json_error("Unable to fetch performance metrics", 404)
    return JsonResponse({"hostid": hostid, "metrics": metrics})


@require_GET
@handle_api_errors
def zabbix_problems(request):
    params = {
        "output": ["eventid", "name", "severity", "acknowledged", "clock"],
        "recent": True,
        "sortfield": "clock",
        "sortorder": "DESC",
    }
    problems = zabbix_request("problem.get", params) or []
    return JsonResponse({"problems": problems, "count": len(problems)})


@require_GET
@handle_api_errors
def zabbix_host_problems(request, hostid: int):
    problems = get_host_problems(hostid) or []
    return JsonResponse({"hostid": hostid, "problems": problems, "count": len(problems)})


@require_GET
@handle_api_errors
def zabbix_events(request):
    params = {
        "output": ["eventid", "name", "severity", "source", "object", "clock"],
        "sortfield": "clock",
        "sortorder": "DESC",
        "limit": 100,
    }
    events = zabbix_request("event.get", params) or []
    return JsonResponse({"events": events, "count": len(events)})


@require_GET
@handle_api_errors
def zabbix_hostgroups(request):
    groups = zabbix_request("hostgroup.get", {"output": ["groupid", "name"]}) or []
    return JsonResponse({"groups": groups, "count": len(groups)})


@require_GET
@handle_api_errors
def zabbix_templates(request):
    templates = zabbix_request("template.get", {"output": ["templateid", "name"]}) or []
    return JsonResponse({"templates": templates, "count": len(templates)})


@require_GET
@handle_api_errors
def zabbix_status(request):
    version = zabbix_request("apiinfo.version", {}) or "unknown"
    return JsonResponse({"version": version})


@require_GET
@handle_api_errors
def zabbix_monitoring_overview(request):
    problems = zabbix_request(
        "problem.get",
        {
            "output": ["severity"],
            "recent": True,
        },
    ) or []
    severity_counter = Counter([p.get("severity", "0") for p in problems])
    return JsonResponse({"open_problems": len(problems), "severity_breakdown": severity_counter})


@require_GET
@handle_api_errors
def zabbix_all_hosts_performance(request):
    hosts = zabbix_request("host.get", {"output": ["hostid", "name"], "filter": {"status": 0}}) or []
    summary = []
    for host in hosts:
        metrics = get_host_performance_metrics(host["hostid"]) or {}
        summary.append({"hostid": host["hostid"], "name": host.get("name", host.get("host")), "metrics": metrics})
    return JsonResponse({"hosts": summary, "count": len(summary)})


@require_GET
@handle_api_errors
def zabbix_hosts_availability(request):
    hosts = zabbix_request("host.get", {"output": ["hostid", "name", "available"]}) or []
    buckets = Counter([host.get("available", "0") for host in hosts])
    return JsonResponse({"totals": buckets, "hosts": hosts})


@require_GET
@handle_api_errors
def zabbix_all_latest_data(request):
    hosts = zabbix_request("host.get", {"output": ["hostid", "name"], "filter": {"status": 0}}) or []
    latest = []
    for host in hosts:
        data = zabbix_request(
            "item.get",
            {
                "output": ["itemid", "name", "lastvalue", "units"],
                "hostids": host["hostid"],
                "filter": {"status": 0},
                "limit": 10,
            },
        ) or []
        latest.append({"hostid": host["hostid"], "name": host.get("name", host.get("host")), "items": data})
    return JsonResponse({"hosts": latest})


@require_GET
@handle_api_errors
def zabbix_problems_summary(request):
    problems = zabbix_request("problem.get", {"output": ["severity", "name"]}) or []
    counter = Counter(p.get("severity", "0") for p in problems)
    return JsonResponse({"summary": counter, "count": len(problems)})


@require_GET
@handle_api_errors
def zabbix_problems_by_severity(request):
    problems = zabbix_request("problem.get", {"output": ["severity", "eventid"]}) or []
    grouped = defaultdict(list)
    for problem in problems:
        grouped[problem.get("severity", "0")].append(problem.get("eventid"))
    return JsonResponse({"by_severity": grouped})


@require_GET
@handle_api_errors
def zabbix_critical_problems(request):
    problems = zabbix_request(
        "problem.get",
        {"output": ["eventid", "name", "clock", "severity"], "filter": {"severity": 5}},
    ) or []
    return JsonResponse({"problems": problems, "count": len(problems)})


@require_GET
@handle_api_errors
def zabbix_recent_events(request):
    events = zabbix_request(
        "event.get",
        {"output": ["eventid", "name", "clock", "severity"], "sortfield": "clock", "sortorder": "DESC", "limit": 50},
    ) or []
    return JsonResponse({"events": events})


@require_GET
@handle_api_errors
def zabbix_events_summary(request):
    events = zabbix_request(
        "event.get",
        {"output": ["eventid", "severity", "clock"], "sortfield": "clock", "sortorder": "DESC", "limit": 200},
    ) or []
    counter = Counter(event.get("severity", "0") for event in events)
    return JsonResponse({"summary": counter, "count": len(events)})


@require_GET
@handle_api_errors
def zabbix_hosts_network_info(request):
    hosts = zabbix_request(
        "host.get",
        {
            "output": ["hostid", "host", "name", "status", "available"],
            "selectInterfaces": ["interfaceid", "ip", "dns", "port", "type"],
            "selectInventory": ["location_lat", "location_lon", "location"],
        },
    ) or []
    return JsonResponse({"hosts": hosts, "count": len(hosts)})


@require_GET
@handle_api_errors
def zabbix_host_network_info(request, hostid: int):
    host_data = zabbix_request(
        "host.get",
        {
            "output": ["hostid", "host", "name", "status", "available"],
            "hostids": hostid,
            "selectInterfaces": "extend",
            "selectInventory": ["location_lat", "location_lon", "location", "contact", "hardware"],
        },
    ) or []
    if not host_data:
        return _json_error("Host not found", 404)
    return JsonResponse(host_data[0])


@require_GET
@handle_api_errors
def zabbix_test(request):
    result = zabbix_request("host.get", {"output": ["hostid", "host"], "limit": 5}) or []
    if result is None:
        return _json_error("Unable to reach Zabbix API", 502)
    return JsonResponse({"status": "success", "hosts_found": len(result), "sample_hosts": result[:3]})


@require_GET
@handle_api_errors
def zabbix_clear_cache(request):
    clear_token_cache()
    return JsonResponse({"status": "success", "message": "Zabbix token cache cleared"})

