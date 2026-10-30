"""Boolean fields from a successful lookup, not internet reachability."""

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription

from .entity import InternetEntity, field

PARALLEL_UPDATES = 0
DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="success", name="Lookup successful", icon="mdi:check-network"
    ),
    BinarySensorEntityDescription(key="is_eu", name="IP country in EU", icon="mdi:flag"),
    BinarySensorEntityDescription(
        key="timezone.is_dst", name="IP daylight saving time", icon="mdi:clock"
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        InternetBinarySensor(entry.runtime_data, entry, description) for description in DESCRIPTIONS
    )


class InternetBinarySensor(InternetEntity, BinarySensorEntity):
    @property
    def is_on(self):
        value = field(self.coordinator.data, self.entity_description.key)
        return value if isinstance(value, bool) else None
