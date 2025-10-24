
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from zabbix_api.guards import reload_diagnostics_flag_cache


@override_settings(ENABLE_DIAGNOSTIC_ENDPOINTS=False)
class DiagnosticsEndpointsDisabledTests(TestCase):
    def setUp(self):
        reload_diagnostics_flag_cache()
        self.env_patch = patch("zabbix_api.guards.env_manager.read_values", return_value={})
        self.runtime_patch = patch(
            "zabbix_api.guards.runtime_settings.get_runtime_config",
            return_value=SimpleNamespace(diagnostics_enabled=False),
        )
        self.env_patch.start()
        self.runtime_patch.start()
        user = get_user_model().objects.create_user("staff", password="pass", is_staff=True)
        self.client.force_login(user)

    def tearDown(self):
        self.env_patch.stop()
        self.runtime_patch.stop()
        reload_diagnostics_flag_cache()

    def test_ping_requires_flag(self):
        response = self.client.get(reverse("zabbix_api:api_test_ping"), {"ip": "127.0.0.1"})
        self.assertEqual(response.status_code, 403)

    def test_telnet_requires_flag(self):
        response = self.client.get(reverse("zabbix_api:api_test_telnet"), {"ip": "127.0.0.1", "port": "80"})
        self.assertEqual(response.status_code, 403)

    def test_ping_telnet_requires_flag(self):
        response = self.client.get(reverse("zabbix_api:api_test_ping_telnet"), {"ip": "127.0.0.1", "port": "80"})
        self.assertEqual(response.status_code, 403)


@override_settings(ENABLE_DIAGNOSTIC_ENDPOINTS=True)
class DiagnosticsEndpointsEnabledTests(TestCase):
    def setUp(self):
        reload_diagnostics_flag_cache()
        self.env_patch = patch(
            "zabbix_api.guards.env_manager.read_values",
            return_value={"ENABLE_DIAGNOSTIC_ENDPOINTS": "true"},
        )
        self.runtime_patch = patch(
            "zabbix_api.guards.runtime_settings.get_runtime_config",
            return_value=SimpleNamespace(diagnostics_enabled=True),
        )
        self.env_patch.start()
        self.runtime_patch.start()
        user = get_user_model().objects.create_user("staff", password="pass", is_staff=True)
        self.client.force_login(user)

    def tearDown(self):
        self.env_patch.stop()
        self.runtime_patch.stop()
        reload_diagnostics_flag_cache()

    @patch("zabbix_api.diagnostics.platform.system", return_value="Windows")
    @patch("zabbix_api.diagnostics.subprocess.run")
    def test_ping_success(self, run_mock, _platform):
        stdout = "Sent = 1, Received = 1, Lost = 0 (0% loss)\nMinimum = 1ms, Maximum = 1ms, Average = 1ms"
        run_mock.return_value = SimpleNamespace(returncode=0, stdout=stdout)

        response = self.client.get(reverse("zabbix_api:api_test_ping"), {"ip": "127.0.0.1", "count": "1"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["received"], 1)

    @patch("zabbix_api.diagnostics.socket.create_connection")
    def test_telnet_success(self, conn_mock):
        class DummySocket:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                pass

            def getpeername(self):
                return ("127.0.0.1", 80)

        conn_mock.return_value = DummySocket()
        response = self.client.get(
            reverse("zabbix_api:api_test_telnet"),
            {"ip": "127.0.0.1", "port": "80", "timeout": "1"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["peername"], ["127.0.0.1", 80])
