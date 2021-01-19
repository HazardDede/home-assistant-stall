"""Detects entities that are in a stalled state."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_PROBLEM,
    BinarySensorEntity,
)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_ENTITIES, CONF_NAME, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
)
from homeassistant.util.dt import now

_LOGGER = logging.getLogger(__name__)


ATTR_ENTITIES = "entities"

DEFAULT_NAME = "Stall"

CONF_THRESHOLD = "threshold"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITIES): [cv.entity_id],
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_THRESHOLD, default=60): cv.positive_int,
    }
)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):
    """Set up the Statistics sensor."""
    _, _ = hass, discovery_info  # Fake usage

    entities = config.get(CONF_ENTITIES)
    name = config.get(CONF_NAME)
    threshold = config.get(CONF_THRESHOLD)

    async_add_entities([StallSensor(entities, name, threshold)], True)

    return True


class StallSensor(BinarySensorEntity):
    """Representation of a Stall sensor."""

    def __init__(self, entities, name, threshold):
        self._entity_ids = entities
        self._name = name
        self._threshold = threshold

        self._state = False
        self._timestamps: Dict[str, datetime] = {}
        self._remove_pit_listener: Optional[CALLBACK_TYPE] = None

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._entity_ids, self._async_state_listener
            )
        )
        self.async_on_remove(self._async_remove_pit_listener)

        self._prepare_initial_map()
        self._schedule_pit_callback()
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_state_listener(self, event):
        """Handle the entity state changes."""
        new_state = event.data.get("new_state")
        if not new_state:
            return

        entity_id = event.data.get("entity_id")
        known_last_changed = self._timestamps.get(entity_id)

        _LOGGER.debug(
            "State change of '%s' observed @ '%s' (known @ '%s')",
            entity_id,
            new_state.last_changed,
            known_last_changed,
        )

        if new_state.last_changed != known_last_changed:
            self._timestamps[entity_id] = new_state.last_changed
            self._schedule_pit_callback()
            self.async_schedule_update_ha_state(True)

    @callback
    def _async_pit_callback(self, data):
        """Handle the Point in time callback to re-evaluate the state."""
        _LOGGER.debug("Point in time callback invoked @ %s", data)
        self._remove_pit_listener = None  # Not valid anymore
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_remove_pit_listener(self):
        if self._remove_pit_listener:
            self._remove_pit_listener()

    def _schedule_pit_callback(self):
        # First remove a possible previous outdated listener
        self._async_remove_pit_listener()

        # Check if and when to trigger the next point in time
        if self._timestamps:
            last_update_ts = max(self._timestamps.values())
            pit = last_update_ts + timedelta(minutes=self._threshold)
            _LOGGER.debug("Schedule next sensor state check @ %s", pit)
            self._remove_pit_listener = async_track_point_in_time(
                self.hass, self._async_pit_callback, pit
            )

    def _prepare_initial_map(self):
        for entity_id in self._entity_ids:
            entity_state = self.hass.states.get(entity_id)
            if entity_state:
                self._timestamps[entity_id] = entity_state.last_changed
                _LOGGER.debug(
                    "Last state change of '%s' @ %s",
                    entity_id,
                    entity_state.last_changed,
                )
            else:
                _LOGGER.warning("Entity '%s' is unknown", entity_id)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self._state

    @property
    def device_class(self) -> str:
        """Return 'problem' to indicate this sensor's device class."""
        return DEVICE_CLASS_PROBLEM

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes of the sensor."""
        return {
            ATTR_ENTITIES: self._timestamps,
        }

    async def async_update(self) -> None:
        """Calculates the latest sensor state."""
        if not self._timestamps:
            self._state = STATE_UNKNOWN
            return

        last_update_ts = max(self._timestamps.values())
        current_ts = now()
        diff_in_minutes = (current_ts - last_update_ts).total_seconds() / 60
        next_state = diff_in_minutes >= self._threshold

        _LOGGER.debug(
            "Threshold check: %s - %s (%s) >= %s (%s)",
            current_ts,
            last_update_ts,
            diff_in_minutes,
            self._threshold,
            "PROBLEM" if next_state else "OK",
        )

        self._state = next_state
