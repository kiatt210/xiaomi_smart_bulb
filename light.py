from homeassistant.components.light import (LightEntity, 
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_COLOR_TEMP)

import voluptuous as vol
from typing import Optional
from functools import partial
import logging

from homeassistant.const import CONF_FILENAME, CONF_HOST, CONF_TOKEN, CONF_NAME
from homeassistant.components.light import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "Xiaomi Smart Bulb"
DATA_KEY = "light.xiaomi_miio"
ATTR_MODEL = "model"
SUCCESS = ["ok"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
        """Set up the light from config."""
        from miio import Device, DeviceException, PhilipsBulb

        if DATA_KEY not in hass.data:
            hass.data[DATA_KEY] = {}

        host = config.get(CONF_HOST)
        name = config.get(CONF_NAME)
        token = config.get(CONF_TOKEN)
        unique_id = "xiao_bulb_"+token[:5]

        #custom_effects = _parse_custom_effects(discovery_info[CONF_CUSTOM_EFFECTS])

        _LOGGER.info("Initializing with host %s (token %s...), name: %s", host, token[:5],name)

        lights = []

        light = PhilipsBulb(host, token)
        device = XiaomiSmartBulb(name, light, unique_id)

        lights.append(device)
        add_entities(lights)
        hass.data[DATA_KEY][host] = light

#    device = XiaomiPhilipsBulb(name, light, model, unique_id)
#    devices.append(device)
#    hass.data[DATA_KEY][host] = device


class XiaomiSmartBulb(LightEntity):


    def __init__(self, name, device, unique_id):
        """Initialize the light device."""
        self._name = name
        self._device = device
        self._unique_id = unique_id
        self._state = None
        self._model = "xiaomi_smart_led"
        self._brightness = None
        self._state_attrs = {ATTR_MODEL: self._model}
        self._available = False
        _LOGGER.error("My name :%s", self._name)


    #def __init__(self, device, custom_effects=None):
        """Initialize the Yeelight light."""
    #    _LOGGER.error("Start initalizing :%s", device)
    #    self.config = device.config
    ##    self._device = device

    #    self._brightness = None
    #    self._color_temp = None
    #    self._hs = None
    #    self._effect = None

    #    self._light_type = LightType.Main

    #    _LOGGER.error("My name :%s", self.name)
    

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def available(self):
        """Return true when state is known."""
        _LOGGER.info("Is available?: %s", self._available)
        return self._available

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if light is on."""
        _LOGGER.info("Is on?: %s", self._state)
        return self._state

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    async def async_update(self):
        _LOGGER.info("async_update")
        """Fetch state from the device."""
        from miio import DeviceException

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)
            return

        _LOGGER.info("Got new state: %s", state)        
        self._available = True
        self._state = state.is_on
        #self._brightness = ceil((255 / 100.0) * state.brightness)


    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a light command handling error messages."""
        _LOGGER.error("Start try comman")
        from miio import DeviceException

        try:
            result = await self.hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )

            _LOGGER.error("Response received from light: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            self._available = False
            return False

    
    def turn_on(self, **kwargs):
        """Turn the device on."""   
        _LOGGER.error("Turn_on")
        self._try_command("Turning the light on failed.", self._device.on)
        self._state=True
    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        _LOGGER.error("Async turn_on")
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            percent_brightness = ceil(100 * brightness / 255.0)

            _LOGGER.debug("Setting brightness: %s %s%%", brightness, percent_brightness)

            result = await self._try_command(
                "Setting brightness failed: %s",
                self._device.set_brightness,
                percent_brightness,
            )

            if result:
                self._brightness = brightness
            self._state=True
        else:
            await self._try_command("Turning the light on failed.", self._device.on)
            self._state=True
    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.error("Turn_off")
        self._try_command("Turning the light off failed.", self._device.off)
        self._state=False
    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        _LOGGER.error("Async turn_off")
        await self._try_command("Turning the light off failed.", self._device.off)
        self._state=False