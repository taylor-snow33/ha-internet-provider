"""All documented free scalar fields, plus complete response attributes."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from .entity import InternetEntity, field

PARALLEL_UPDATES = 0
DESCRIPTIONS = (
    SensorEntityDescription(key="ip", name="Public IP", icon="mdi:ip-network"),
    SensorEntityDescription(
        key="type", name="IP version", icon="mdi:ip", entity_category=EntityCategory.DIAGNOSTIC
    ),
    SensorEntityDescription(key="connection.isp", name="ISP", icon="mdi:web"),
    SensorEntityDescription(key="connection.org", name="Network organization", icon="mdi:domain"),
    SensorEntityDescription(key="connection.asn", name="ASN", icon="mdi:identifier"),
    SensorEntityDescription(key="connection.domain", name="Network domain", icon="mdi:web"),
    SensorEntityDescription(key="continent", name="Continent", icon="mdi:earth"),
    SensorEntityDescription(key="continent_code", name="Continent code", icon="mdi:earth"),
    SensorEntityDescription(key="country", name="Country", icon="mdi:flag"),
    SensorEntityDescription(key="country_code", name="Country code", icon="mdi:flag"),
    SensorEntityDescription(key="region", name="Region", icon="mdi:map"),
    SensorEntityDescription(key="region_code", name="Region code", icon="mdi:map"),
    SensorEntityDescription(key="city", name="City", icon="mdi:city"),
    SensorEntityDescription(key="latitude", name="IP latitude", icon="mdi:latitude"),
    SensorEntityDescription(key="longitude", name="IP longitude", icon="mdi:longitude"),
    SensorEntityDescription(key="postal", name="Postal code", icon="mdi:mailbox"),
    SensorEntityDescription(key="calling_code", name="Calling code", icon="mdi:phone"),
    SensorEntityDescription(key="capital", name="Capital", icon="mdi:city"),
    SensorEntityDescription(key="borders", name="Bordering country codes", icon="mdi:map"),
    SensorEntityDescription(
        key="flag.img",
        name="Flag image URL",
        icon="mdi:flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(key="flag.emoji", name="Flag emoji", icon="mdi:flag"),
    SensorEntityDescription(
        key="flag.emoji_unicode",
        name="Flag Unicode",
        icon="mdi:flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(key="timezone.id", name="IP time zone", icon="mdi:map-clock"),
    SensorEntityDescription(key="timezone.abbr", name="Time zone abbreviation", icon="mdi:clock"),
    SensorEntityDescription(key="timezone.offset", name="UTC offset seconds", icon="mdi:clock"),
    SensorEntityDescription(key="timezone.utc", name="UTC offset", icon="mdi:clock"),
    SensorEntityDescription(
        key="timezone.current_time",
        name="Provider timestamp",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        InternetSensor(entry.runtime_data, entry, description) for description in DESCRIPTIONS
    )


class InternetSensor(InternetEntity, SensorEntity):
    @property
    def native_value(self):
        value = field(self.coordinator.data, self.entity_description.key)
        if self.entity_description.key == "timezone.current_time":
            parsed = dt_util.parse_datetime(value) if isinstance(value, str) else None
            return parsed if parsed is not None and parsed.tzinfo is not None else None
        if isinstance(value, str):
            return value[:255]
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    @property
    def extra_state_attributes(self):
        if self.entity_description.key == "ip" and self.available:
            return {
                "response": self.coordinator.data,
                "last_successful_lookup": self.coordinator.last_success.isoformat(),
            }
        return None
