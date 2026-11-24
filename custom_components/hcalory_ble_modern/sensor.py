"""Expose only established protocol fields."""
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .protocol import STATE_OPTIONS

DESCRIPTIONS = (
    SensorEntityDescription(
        key="state", translation_key="state", icon="mdi:radiator",
        device_class=SensorDeviceClass.ENUM, options=STATE_OPTIONS,
    ),
    SensorEntityDescription(key="level", translation_key="level", icon="mdi:fire"),
    SensorEntityDescription(key="state_raw", translation_key="state_raw", entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="mode_raw", translation_key="mode_raw", entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(HeaterSensor(entry.runtime_data, entry, desc) for desc in DESCRIPTIONS)


class HeaterSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)}, name=entry.title,
            manufacturer="Hcalory", model="BD39 controller (experimental)",
        )

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self.entity_description.key)
