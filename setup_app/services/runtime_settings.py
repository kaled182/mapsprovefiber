from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from django.conf import settings

from setup_app.models import FirstTimeSetup


@dataclass
class RuntimeConfig:
    zabbix_api_url: str
    zabbix_api_user: str
    zabbix_api_password: str
    zabbix_api_key: str
    google_maps_api_key: str
    allowed_hosts: list[str]
    diagnostics_enabled: bool


def _fallback_config() -> RuntimeConfig:
    allowed_hosts = settings.ALLOWED_HOSTS if isinstance(settings.ALLOWED_HOSTS, (list, tuple)) else []
    return RuntimeConfig(
        zabbix_api_url=getattr(settings, "ZABBIX_API_URL", ""),
        zabbix_api_user=getattr(settings, "ZABBIX_API_USER", ""),
        zabbix_api_password=getattr(settings, "ZABBIX_API_PASSWORD", ""),
        zabbix_api_key=getattr(settings, "ZABBIX_API_KEY", ""),
        google_maps_api_key=getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
        allowed_hosts=list(allowed_hosts),
        diagnostics_enabled=getattr(settings, "ENABLE_DIAGNOSTIC_ENDPOINTS", False),
    )


@lru_cache(maxsize=1)
def get_runtime_config() -> RuntimeConfig:
    record = FirstTimeSetup.objects.filter(configured=True).order_by("-configured_at").first()
    if not record:
        return _fallback_config()

    allowed_hosts_env = settings.ALLOWED_HOSTS if isinstance(settings.ALLOWED_HOSTS, (list, tuple)) else []
    return RuntimeConfig(
        zabbix_api_url=record.zabbix_url or getattr(settings, "ZABBIX_API_URL", ""),
        zabbix_api_user=record.zabbix_user or getattr(settings, "ZABBIX_API_USER", ""),
        zabbix_api_password=record.zabbix_password or getattr(settings, "ZABBIX_API_PASSWORD", ""),
        zabbix_api_key=record.zabbix_api_key or getattr(settings, "ZABBIX_API_KEY", ""),
        google_maps_api_key=record.maps_api_key or getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
        allowed_hosts=list(allowed_hosts_env),
        diagnostics_enabled=getattr(settings, "ENABLE_DIAGNOSTIC_ENDPOINTS", False),
    )


def reload_config() -> None:
    get_runtime_config.cache_clear()

