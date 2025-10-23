from __future__ import annotations

from django.db import models
from django.utils import timezone


class Site(models.Model):
    name = models.CharField(max_length=120, unique=True)
    city = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Device(models.Model):
    site = models.ForeignKey(Site, related_name="devices", on_delete=models.CASCADE)
    device_icon = models.ImageField(upload_to="img/device_icons/", null=True, blank=True)
    name = models.CharField(max_length=120)
    vendor = models.CharField(max_length=120, blank=True)
    model = models.CharField(max_length=120, blank=True)
    zabbix_hostid = models.CharField(max_length=32, blank=True, help_text="hostid inside Zabbix")
    uptime_item_key = models.CharField(
        max_length=255, blank=True, help_text="Zabbix item key for uptime (e.g. system.uptime)"
    )
    cpu_usage_item_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="Zabbix item key for CPU usage (e.g. system.cpu.util[,user])",
    )

    class Meta:
        unique_together = ("site", "name")
        ordering = ["site__name", "name"]

    def __str__(self) -> str:
        return f"{self.site.name} - {self.name}" if self.site_id else self.name


class Port(models.Model):
    device = models.ForeignKey(Device, related_name="ports", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    zabbix_item_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="Zabbix interface item key (e.g. net.if.in[ether10])",
    )
    zabbix_item_id_trafego_in = models.CharField(
        max_length=32,
        blank=True,
        help_text="Zabbix itemid for ingress traffic",
    )
    zabbix_item_id_trafego_out = models.CharField(
        max_length=32,
        blank=True,
        help_text="Zabbix itemid for egress traffic",
    )
    zabbix_interfaceid = models.CharField(max_length=32, blank=True, help_text="interfaceid inside Zabbix")
    zabbix_itemid = models.CharField(max_length=32, blank=True, help_text="Generic itemid inside Zabbix")
    # Optional optical power items (RX/TX) leveraged when ifOperStatus is missing
    rx_power_item_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optical RX power item key (e.g. hwEntityOpticalLaneRxPower[ID])",
    )
    tx_power_item_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optical TX power item key (e.g. hwEntityOpticalLaneTxPower[ID])",
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("device", "name")
        ordering = ["device__site__name", "device__name", "name"]

    def __str__(self) -> str:
        return f"{self.device}::{self.name}"

    # Backwards compatibility helpers: expose English attribute names while reusing legacy fields
    @property
    def zabbix_item_id_traffic_in(self) -> str:
        return getattr(self, "zabbix_item_id_trafego_in", "")

    @zabbix_item_id_traffic_in.setter
    def zabbix_item_id_traffic_in(self, value: str) -> None:
        self.zabbix_item_id_trafego_in = value

    @property
    def zabbix_item_id_traffic_out(self) -> str:
        return getattr(self, "zabbix_item_id_trafego_out", "")

    @zabbix_item_id_traffic_out.setter
    def zabbix_item_id_traffic_out(self, value: str) -> None:
        self.zabbix_item_id_trafego_out = value


class FiberCable(models.Model):
    STATUS_UP = "up"
    STATUS_DOWN = "down"
    STATUS_DEGRADED = "degraded"
    STATUS_UNKNOWN = "unknown"
    STATUS_CHOICES = [
        (STATUS_UP, "Operational"),
        (STATUS_DOWN, "Unavailable"),
        (STATUS_DEGRADED, "Degraded"),
        (STATUS_UNKNOWN, "Unknown"),
    ]

    name = models.CharField(max_length=150, unique=True)
    origin_port = models.ForeignKey(Port, related_name="fiber_origin", on_delete=models.PROTECT)
    destination_port = models.ForeignKey(Port, related_name="fiber_destination", on_delete=models.PROTECT)
    length_km = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    # List of intermediate coordinates used when plotting the route (may include origin/destination)
    path_coordinates = models.JSONField(
        blank=True,
        null=True,
        help_text="Coordinate list [{'lat': -16.6, 'lng': -49.2}, ...]",
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_UNKNOWN)
    last_status_update = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def update_status(self, new_status: str) -> None:
        if new_status not in dict(self.STATUS_CHOICES):
            new_status = self.STATUS_UNKNOWN
        self.status = new_status
        self.last_status_update = timezone.now()
        self.save(update_fields=["status", "last_status_update"])


class FiberEvent(models.Model):
    fiber = models.ForeignKey(FiberCable, related_name="events", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    previous_status = models.CharField(max_length=15, blank=True)
    new_status = models.CharField(max_length=15)
    detected_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.fiber.name} {self.previous_status}->{self.new_status} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"
