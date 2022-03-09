"""Platform for sensor integration."""
from __future__ import annotations
from tokenize import Number
from xmlrpc.client import Boolean

import aiohttp
import logging
import voluptuous as vol
from datetime import timedelta
from typing import Any, Callable, Dict, Optional

from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
        SensorDeviceClass,
        SensorEntity,
        SensorStateClass,
        PLATFORM_SCHEMA,
)
from homeassistant.const import (
        CONF_USERNAME,
        CONF_PASSWORD,
        ENERGY_KILO_WATT_HOUR,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt

from .const import (
    CHILICON_URL,
    CONF_INSTALLATION_HASH,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_INSTALLATION_HASH): cv.string,
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    user = discovery_info[CONF_USERNAME]
    pw = discovery_info[CONF_PASSWORD]
    hash = discovery_info[CONF_INSTALLATION_HASH]

    _LOGGER.debug("running chilicon_cloud.async_setup_platform()")
    session = async_get_clientsession(hass)
    cc = ChiliconCloud(session, user, pw, hash)
    await cc.login()

    async_add_entities([ChiliconSensor(cc)], update_before_add=True)


class ChiliconSensor(SensorEntity):
    """Representation of a sensor."""

    _attr_name = "Chilicon power daily"
    _attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, cc: ChiliconCloud):
        _LOGGER.debug("in ChiliconSensor.__init__()")
        self.cc = cc

    async def async_update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        kwh = await self.cc.fetch_data(retry=True)
        if kwh == -1:
            _LOGGER.warn("no value returned from chilicon, using last value instead")
            kwh = self.hass.data[DOMAIN]['energy']
            if not kwh:
                _LOGGER.warn("no saved value for energy found, returning early")
                return
        else:
            # Save the value back to data so we can use it in the future
            self.hass.data[DOMAIN]['energy'] = kwh

        self._attr_native_value = kwh
        _LOGGER.debug("updated energy: {}".format(kwh))

class ChiliconCloud():
    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        installation_hash: str
    ):
        self.session = session
        self.username = username
        self.password = password
        self.installation_hash = installation_hash

    async def login(self) -> Boolean:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        form_data = {
            'username': self.username,
            'password': self.password,
            'Login': 'Login'
        }

        async with self.session.post(CHILICON_URL + '/login', data=form_data, headers=headers, allow_redirects=False) as resp:
            loc = resp.headers['Location']
            expected = "/installation/{}".format(self.installation_hash)
            if expected != loc:
                _LOGGER.warn("Unexpected installation hash. Got: {}".format(loc))
                return False
            return True

    async def fetch_data(self, retry: Boolean) -> float:
        _LOGGER.debug("Invoking ChiliconCloud.fetch_data()")

        dt_local = dt.now()
        today = dt_local.strftime("%Y-%m-%d")

        headers = {
            'Host': 'cloud.chiliconpower.com',
            'Referer': "{}/installation/{}".format(CHILICON_URL, self.installation_hash)
        }

        updateUrl = "{}/ajax/fetchOwnerUpdate?today={}".format(CHILICON_URL, today)
        async with self.session.get(updateUrl, headers=headers) as resp:
            if resp.status != 200:
                _LOGGER.warn("status code is not 200: {}".format(resp.status))

                if (resp.status == 400 or resp.status == 401) and retry:
                    await self.login()
                    _LOGGER.info("retrying fetch_data() after login")
                    return await self.fetch_data(retry=False)

                return -1
            
            [day_data, lifetime, current] = await resp.json()
            kwh = self.calculate_today(day_data)
            return kwh

    def calculate_today(self, today_data):
        # The today array contains the average power generated for each 5 minute
        # period of the day. A value of -1 means that twe can ignore that data point
        # either because it is in the future or because no power was generated in
        # that time. All of the readings are in watts.
        # To get the number of kilowatt-hours generated in a day, sum up all of the
        # readings divided by 12000. (Each 5 minute period is 1/12 of an hour, and
        # each watt is 1/1000 of a kilowatt)
        sum = 0.0
        for p in today_data:
            if p == -1:
                continue
            sum += (p / 12000)

        return sum