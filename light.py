from homeassistant.components.light import (LightEntity, 
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    SUPPORT_COLOR_TEMP,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    ATTR_HS_COLOR,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR)

import voluptuous as vol
from math import ceil
from typing import Optional
from functools import partial
import logging
from typing import Tuple

from homeassistant.const import CONF_FILENAME, CONF_HOST, CONF_TOKEN, CONF_NAME
from homeassistant.components.light import PLATFORM_SCHEMA
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import homeassistant.helpers.config_validation as cv

from homeassistant.util.color import (
    color_temperature_kelvin_to_mired as kelvin_to_mired,
    color_temperature_mired_to_kelvin as mired_to_kelvin,
)

from homeassistant.util import color

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "Xiaomi Smart Bulb"
DATA_KEY = "light.xiaomi_miio"
ATTR_MODEL = "model"
SUCCESS = ["ok"]

CCT_MIN = 1
CCT_MAX = 100

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
        """Set up the light from config."""
        from miio import Device, DeviceException, Yeelight, PhilipsMoonlight

        if DATA_KEY not in hass.data:
            hass.data[DATA_KEY] = {}

        host = config.get(CONF_HOST)
        name = config.get(CONF_NAME)
        token = config.get(CONF_TOKEN)
        unique_id = "xiao_bulb_"+token[:5]

        _LOGGER.info("Initializing with host %s (token %s...), name: %s", host, token[:5],name)

        lights = []

        yeelight = Yeelight(host, token)
        device = XiaomiSmartBulb(name, yeelight, unique_id)

        lights.append(device)
        add_entities(lights)
        hass.data[DATA_KEY][host] = yeelight


class XiaomiSmartBulb(LightEntity):


    def __init__(self, name, yeelight_device, unique_id):
        """Initialize the light device."""
        self._name = name
        self._yeelight_device = yeelight_device
        self._unique_id = unique_id
        self._state = None
        self._color_temp = None
        self._rgb = None
        self._model = "xiaomi_smart_led"
        self._brightness = None
        self._state_attrs = {ATTR_MODEL: self._model}
        self._available = False

    @staticmethod
    def translate(value, left_min, left_max, right_min, right_max):
        """Map a value from left span to right span."""
        left_span = left_max - left_min
        right_span = right_max - right_min
        value_scaled = float(value - left_min) / float(left_span)
        _LOGGER.debug("Translate result :%s", int(right_min + (value_scaled * right_span)) )
        return int(right_min + (value_scaled * right_span)) 

    @staticmethod
    def translate_to_value(percent, min, max):
        """Translate percentage to value """
        scale = max -min
        _LOGGER.debug("Translate %s, %s, %s result: %s", percent,min,max, int (value = percent * (scale/100)))
        return int (value = percent * (scale/100))
    
    @staticmethod
    def rgb_to_int(x: Tuple[int, int, int]) -> int:
        """Return an integer from RGB tuple."""
        return int(x[0] << 16 | x[1] << 8 | x[2])

    @property
    def supported_features(self):
        """Return the supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_COLOR

    @property
    def should_poll(self):
        """No polling needed."""
        return True

    @property
    def available(self):
        """Return true when state is known."""
        _LOGGER.debug("Is available?: %s", self._available)
        return self._available

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if light is on."""
        _LOGGER.debug("Is on?: %s", self._state)
        return self._state

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name
    @property
    def color_temp(self):
        """Return the CT color value in mireds."""
        _LOGGER.debug("Return color temp: %s", self._color_temp)
        return self._color_temp
    
    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        _LOGGER.debug("Return brightness: %s", self._brightness)
        return self._brightness

    @property
    def min_mireds(self):
        """Return the coldest color_temp that this light supports."""
        return 1700

    @property
    def max_mireds(self):
        """Return the warmest color_temp that this light supports."""
        return 6500

    async def async_update(self):
        _LOGGER.debug("async_update")
        """Fetch state from the device."""
        from miio import DeviceException

        try:
            yeelight_state = await self.hass.async_add_executor_job(self._yeelight_device.status)
        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)
            return

        _LOGGER.debug("Got new yeelight state: %s", yeelight_state)
        self._available = True
        self._state = yeelight_state.is_on
        self._brightness = ceil((255 / 100.0) * yeelight_state.brightness)
        if yeelight_state.color_temp is not None:
            self._color_temp = 6500-(abs(yeelight_state.color_temp-1700))
        self._rgb = yeelight_state.rgb

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a light command handling error messages."""
        _LOGGER.debug("Start try command")
        from miio import DeviceException

        try:
            result = await self.hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )

            _LOGGER.debug("Response received from light: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            self._available = False
            return False
    
    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self._try_command("Turning the light on failed.", self._yeelight_device.on)
        if ATTR_COLOR_TEMP in kwargs:
            color_temp = kwargs[ATTR_COLOR_TEMP]
            percent_color_temp = self.translate(
                color_temp, self.max_mireds, self.min_mireds, CCT_MIN, CCT_MAX
            )
            
            device_color_temp = 6500 - (abs(color_temp - 1700))

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            percent_brightness = ceil(100 * brightness / 255.0)
        
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
        
        if ATTR_HS_COLOR in kwargs:
            hs_color = kwargs[ATTR_HS_COLOR]
            rgb = color.color_hs_to_RGB(*hs_color)

        if ATTR_BRIGHTNESS in kwargs and ATTR_COLOR_TEMP in kwargs:
            _LOGGER.debug(
                "Setting brightness and color temperature: "
                "%s %s%%, %s mireds, %s%% cct",
                brightness,
                percent_brightness,
                device_color_temp,
                percent_color_temp,
            )

            result = await self._try_command(
                "Setting brightness and color temperature failed: " "%s bri, %s cct",
                self._yeelight_device.set_brightness_and_color_temperature,
                percent_brightness,
                percent_color_temp,
            )

            if result:
                self._color_temp = state.color_temp
                self._brightness = brightness

        elif ATTR_COLOR_TEMP in kwargs:
            _LOGGER.debug(
                "Setting color temperature: " "%s mireds, %s%% cct",
                device_color_temp,
                percent_color_temp,
            )

            result = await self._try_command(
                "Setting color temperature failed: %s cct",
                self._yeelight_device.set_color_temp,
                device_color_temp,
            )

            if result:
                self._color_temp = color_temp                                  

        elif ATTR_RGB_COLOR in kwargs or ATTR_HS_COLOR in kwargs:
            _LOGGER.debug("Set rgb color to:set_rgb '["+str(rgb)+",\"smooth\",500]'")

            result = await self._try_command(
                "Setting rgb failed: %s",
                self._yeelight_device.set_rgb, rgb
            )

            if result:
                self._rgb = rgb

        elif ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            percent_brightness = ceil(100 * brightness / 255.0)

            _LOGGER.debug("Setting brightness: %s %s%%", brightness, percent_brightness)

            result = await self._try_command(
                "Setting brightness failed: %s",
                self._yeelight_device.set_brightness,
                percent_brightness,
            )

            if result:
                self._brightness = brightness

    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.debug("Turn_off")
        self._try_command("Turning the light off failed.", self._yeelight_device.off)
        self._state=False
    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        _LOGGER.debug("Async turn_off")
        await self._try_command("Turning the light off failed.", self._yeelight_device.off)
        self._state=False
