"""Example Load Platform integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from homeassistant.const import (
        CONF_USERNAME,
        CONF_PASSWORD,
)

from .const import (
    CONF_INSTALLATION_HASH,
    DOMAIN,
)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Your controller/hub specific code."""
    # Data that you want to share with your platforms
    hass.data[DOMAIN] = {
        'energy': 0
    }

    # Config was always null in sensor.async_load_platform(), so
    # passing the configuration data via discovery_info instead
    discovery_info = {
        CONF_USERNAME: config[DOMAIN][CONF_USERNAME],
        CONF_PASSWORD: config[DOMAIN][CONF_PASSWORD],
        CONF_INSTALLATION_HASH: config[DOMAIN][CONF_INSTALLATION_HASH],
    }
    hass.helpers.discovery.load_platform('sensor', DOMAIN, discovery_info, config)

    return True

