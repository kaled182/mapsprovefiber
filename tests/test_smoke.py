import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from django.test import Client

def test_health():
    c = Client()
    r = c.get("/health/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_dashboard_route_exists():
    c = Client()
    r = c.get("/maps_view/dashboard/")
    assert r.status_code in (200, 302)  # 302 se exigir login
