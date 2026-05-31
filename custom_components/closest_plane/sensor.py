"""Sensor platform for Closest Plane."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfSpeed, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClosestPlaneCoordinator


@dataclass(frozen=True, kw_only=True)
class ClosestPlaneSensorDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with the data key to read."""
    data_key: str = ""
    extra_attributes_key: bool = False


SENSORS: tuple[ClosestPlaneSensorDescription, ...] = (
    ClosestPlaneSensorDescription(
        key="callsign",
        data_key="callsign",
        name="Callsign",
        icon="mdi:airplane",
        extra_attributes_key=True,
    ),
    ClosestPlaneSensorDescription(
        key="flight_number",
        data_key="flight_number",
        name="Flight number",
        icon="mdi:airplane-takeoff",
    ),
    ClosestPlaneSensorDescription(
        key="airline",
        data_key="airline",
        name="Airline",
        icon="mdi:office-building",
    ),
    ClosestPlaneSensorDescription(
        key="departure",
        data_key="departure",
        name="Departure",
        icon="mdi:airplane-takeoff",
    ),
    ClosestPlaneSensorDescription(
        key="destination",
        data_key="destination",
        name="Destination",
        icon="mdi:airplane-landing",
    ),
    ClosestPlaneSensorDescription(
        key="registration",
        data_key="registration",
        name="Registration",
        icon="mdi:identifier",
    ),
    ClosestPlaneSensorDescription(
        key="aircraft_type",
        data_key="aircraft_type",
        name="Aircraft type",
        icon="mdi:airplane",
    ),
    ClosestPlaneSensorDescription(
        key="aircraft_model",
        data_key="aircraft_model",
        name="Aircraft model",
        icon="mdi:airplane",
    ),
    ClosestPlaneSensorDescription(
        key="distance_km",
        data_key="distance_km",
        name="Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
    ),
    ClosestPlaneSensorDescription(
        key="altitude_ft",
        data_key="altitude_ft",
        name="Altitude",
        native_unit_of_measurement="ft",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:altimeter",
    ),
    ClosestPlaneSensorDescription(
        key="speed_knots",
        data_key="speed_knots",
        name="Speed",
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
    ),
    ClosestPlaneSensorDescription(
        key="heading",
        data_key="heading",
        name="Heading",
        native_unit_of_measurement="°",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass",
    ),
    ClosestPlaneSensorDescription(
        key="vertical_rate_fpm",
        data_key="vertical_rate_fpm",
        name="Vertical rate",
        native_unit_of_measurement="ft/min",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-up-down",
    ),
    ClosestPlaneSensorDescription(
        key="remaining_minutes",
        data_key="remaining_minutes",
        name="Remaining flight time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:clock-end",
    ),
    ClosestPlaneSensorDescription(
        key="elapsed_minutes",
        data_key="elapsed_minutes",
        name="Elapsed flight time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:clock-start",
    ),
    ClosestPlaneSensorDescription(
        key="icao24",
        data_key="icao24",
        name="ICAO24",
        icon="mdi:hexadecimal",
    ),
    ClosestPlaneSensorDescription(
        key="origin_country",
        data_key="origin_country",
        name="Origin country",
        icon="mdi:flag",
    ),
    ClosestPlaneSensorDescription(
        key="squawk",
        data_key="squawk",
        name="Squawk",
        icon="mdi:radio",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ClosestPlaneCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ClosestPlaneSensor(coordinator, entry, description) for description in SENSORS
    )


class ClosestPlaneSensor(CoordinatorEntity[ClosestPlaneCoordinator], SensorEntity):
    """One sensor entity representing a single field of the closest aircraft."""

    entity_description: ClosestPlaneSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ClosestPlaneCoordinator,
        entry: ConfigEntry,
        description: ClosestPlaneSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Closest Plane",
            manufacturer="OpenSky Network",
            model="Aircraft Monitor",
        )

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self.entity_description.data_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.entity_description.extra_attributes_key or not self.coordinator.data:
            return None
        d = self.coordinator.data
        return {
            "departure_airport": d.get("departure_airport"),
            "destination_airport": d.get("destination_airport"),
            "scheduled_departure": d.get("scheduled_departure"),
            "actual_departure": d.get("actual_departure"),
            "scheduled_arrival": d.get("scheduled_arrival"),
            "estimated_arrival": d.get("estimated_arrival"),
            "total_minutes": d.get("total_minutes"),
            "latitude": d.get("latitude"),
            "longitude": d.get("longitude"),
            "confidence": d.get("confidence"),
            "sources": d.get("sources"),
        }
