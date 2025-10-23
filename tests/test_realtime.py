from __future__ import annotations

from asyncio import CancelledError

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import AsyncMock, patch

from core.asgi import application
from maps_view.realtime.consumers import DashboardStatusConsumer
from maps_view.realtime.events import build_dashboard_payload
from maps_view.realtime.publisher import DASHBOARD_STATUS_GROUP, broadcast_dashboard_status
from maps_view.tasks import broadcast_dashboard_snapshot


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class DashboardRealtimeTests(TestCase):
    def test_consumer_rejects_anonymous_connections(self):
        communicator = WebsocketCommunicator(application, "/ws/dashboard/status/")
        connected, close_code = async_to_sync(communicator.connect)()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)
        # No explicit disconnect needed since handshake was rejected.

    def test_authenticated_connection_succeeds(self):
        user = get_user_model().objects.create_user("ws-ok", password="pass")
        communicator = WebsocketCommunicator(application, "/ws/dashboard/status/")
        communicator.scope["user"] = user

        connected, _ = async_to_sync(communicator.connect)()
        self.assertTrue(connected)

        try:
            async_to_sync(communicator.disconnect)()
        except CancelledError:
            pass

    def test_authenticated_client_receives_broadcast(self):
        hosts_status_data = {
            "hosts_status": [{"device_id": "1", "available": "1"}],
            "hosts_summary": {"total": 1, "available": 1, "unavailable": 0, "unknown": 0},
        }

        payload = build_dashboard_payload(hosts_status_data)
        consumer = DashboardStatusConsumer()
        consumer.scope = {"user": None}
        consumer.channel_name = "test-channel"
        consumer.send_json = AsyncMock()

        async_to_sync(consumer.dashboard_status)({"payload": payload})
        consumer.send_json.assert_awaited_once_with(payload)

    def test_broadcast_helper_queues_message(self):
        messages = []

        class DummyLayer:
            async def group_send(self, group, message):
                messages.append((group, message))

        with patch("maps_view.realtime.publisher.get_channel_layer", return_value=DummyLayer()):
            hosts_status_data = {
                "hosts_status": [],
                "hosts_summary": {"total": 0, "available": 0, "unavailable": 0, "unknown": 0},
            }
            result = broadcast_dashboard_status(hosts_status_data)

        self.assertTrue(result)
        self.assertEqual(messages[0][0], DASHBOARD_STATUS_GROUP)

    def test_event_builder_shapes_payload(self):
        data = {
            "hosts_status": [{"device_id": "2", "available": "2"}],
            "hosts_summary": {"total": 1, "available": 0, "unavailable": 1, "unknown": 0},
        }
        payload = build_dashboard_payload(data)
        self.assertEqual(payload["event"], "dashboard.status")
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["data"]["hosts"], data["hosts_status"])

    def test_broadcast_snapshot_task(self):
        snapshot = {"hosts_status": [{"name": "Device"}], "hosts_summary": {"total": 1}}
        with patch("maps_view.tasks.get_hosts_status_data", return_value=snapshot) as get_data, patch(
            "maps_view.tasks.broadcast_dashboard_status", return_value=True
        ) as broadcaster:
            result = broadcast_dashboard_snapshot.run()

        self.assertTrue(result["broadcasted"])
        get_data.assert_called_once()
        broadcaster.assert_called_once_with(snapshot)

    def test_hosts_status_api_returns_payload(self):
        user = get_user_model().objects.create_user("api-user", password="pass")
        sample = {
            "hosts_status": [{"name": "WRK-01", "status_class": "bg-green-100", "color": "#16a34a"}],
            "hosts_summary": {"total": 1, "available": 1, "unavailable": 0, "unknown": 0},
        }
        self.client.force_login(user)

        with patch("maps_view.views.get_hosts_status_data", return_value=sample):
            response = self.client.get(reverse("maps_view:api_hosts_status"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(len(payload["hosts"]), 1)

