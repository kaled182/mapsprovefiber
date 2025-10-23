# core/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def zabbix_lookup_page(request):
    """
    Render the Zabbix lookup integration page.
    The frontend consumes the REST endpoints from the zabbix_api app.
    """
    return render(request, "zabbix/lookup.html")
