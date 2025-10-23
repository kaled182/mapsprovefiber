from django.contrib import admin
from .models import Site, Device, Port, FiberCable, FiberEvent


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
	list_display = ("name", "city", "latitude", "longitude")
	search_fields = ("name", "city")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
	list_display = ("name", "site", "vendor", "model", "zabbix_hostid")
	list_filter = ("site", "vendor")
	search_fields = ("name", "zabbix_hostid")


@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
	list_display = ("name", "device", "zabbix_item_key")
	list_filter = ("device__site",)
	search_fields = ("name", "device__name", "zabbix_item_key")


@admin.register(FiberCable)
class FiberCableAdmin(admin.ModelAdmin):
	list_display = ("name", "origin_port", "destination_port", "length_km", "status", "last_status_update")
	list_filter = ("status",)
	search_fields = ("name", "origin_port__device__name", "destination_port__device__name")


@admin.register(FiberEvent)
class FiberEventAdmin(admin.ModelAdmin):
	list_display = ("fiber", "timestamp", "previous_status", "new_status", "detected_reason")
	list_filter = ("new_status", "timestamp")
	search_fields = ("fiber__name", "detected_reason")

