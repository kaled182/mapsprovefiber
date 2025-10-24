from __future__ import annotations

from django import forms


class FirstTimeSetupForm(forms.Form):
    company_name = forms.CharField(label="Company name", max_length=255)
    logo = forms.ImageField(label="Company logo (PNG)", required=True)
    zabbix_url = forms.CharField(label="Zabbix URL", max_length=255)
    auth_type = forms.ChoiceField(
        label="Authentication method",
        choices=[("token", "Zabbix API token"), ("login", "Zabbix user and password")],
        widget=forms.RadioSelect,
    )
    zabbix_api_key = forms.CharField(label="Zabbix API key", max_length=255, required=False)
    zabbix_user = forms.CharField(label="Zabbix user", max_length=255, required=False)
    zabbix_password = forms.CharField(
        label="Zabbix password",
        max_length=255,
        required=False,
        widget=forms.PasswordInput,
    )
    maps_api_key = forms.CharField(label="Google Maps API key", max_length=255)
    unique_licence = forms.CharField(label="License key", max_length=255)


class EnvConfigForm(forms.Form):
    secret_key = forms.CharField(
        label="SECRET_KEY",
        max_length=255,
        help_text="Restart the server after changing this value.",
    )
    debug = forms.BooleanField(
        label="DEBUG",
        required=False,
        help_text="Disable in production to avoid leaking sensitive information.",
    )
    zabbix_api_url = forms.CharField(label="ZABBIX_API_URL", max_length=255)
    zabbix_api_user = forms.CharField(label="ZABBIX_API_USER", max_length=255, required=False)
    zabbix_api_password = forms.CharField(
        label="ZABBIX_API_PASSWORD",
        max_length=255,
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )
    zabbix_api_key = forms.CharField(
        label="ZABBIX_API_KEY",
        max_length=255,
        required=False,
        help_text="Use when authenticating via API token.",
    )
    google_maps_api_key = forms.CharField(label="GOOGLE_MAPS_API_KEY", max_length=255, required=False)
    allowed_hosts = forms.CharField(
        label="ALLOWED_HOSTS",
        max_length=255,
        required=False,
        help_text="Comma separated. Example: localhost,127.0.0.1,example.com",
    )
    enable_diagnostics = forms.BooleanField(
        label="ENABLE_DIAGNOSTIC_ENDPOINTS",
        required=False,
        help_text="Allow diagnostic endpoints (ping/telnet).",
    )

    def clean_allowed_hosts(self) -> str:
        value = self.cleaned_data.get("allowed_hosts", "")
        parts = [host.strip() for host in value.split(",") if host.strip()]
        return ",".join(parts)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_class = (
            "rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none "
            "focus:ring focus:ring-blue-500/20 w-full"
        )
        checkbox_class = "h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", checkbox_class)
            else:
                field.widget.attrs.setdefault("class", base_class)
