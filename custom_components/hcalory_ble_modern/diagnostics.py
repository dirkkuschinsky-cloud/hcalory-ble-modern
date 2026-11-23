"""Minimal diagnostics with no Bluetooth address, device name or raw capture."""
from dataclasses import asdict


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    client = coordinator.heater.client
    return {
        "integration_version": "0.1.0-alpha.2",
        "protocol": "BD39/BDF8",
        "last_update_success": coordinator.last_update_success,
        "connected": bool(client and client.is_connected),
        "status": asdict(coordinator.data) if coordinator.data else None,
    }
