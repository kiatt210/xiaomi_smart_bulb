# xiaomi_smart_bulb
Xiaomi Smart Bulb (MJDPL01YL) Home Assistant integration

### Token
The integration needs the token of the light, the can be obtained by various methods. The most simple that I have found is:
"The easiest way to obtain tokens is to browse through log files of the Mi Home app version 5.4.49 for Android. It seems that version was released with debug messages turned on by mistake. An APK file with the old version can be easily found using one of the popular web search engines. After downgrading use a file browser to navigate to directory SmartHome/logs/plug_DeviceManager, then open the most recent file and search for the token. When finished, use Google Play to get the most recent version back."
(source:https://python-miio.readthedocs.io/en/latest/discovery.html#logged-tokens)

### Installation

Install it as you would do with any homeassistant custom component:

1. Clone repository.
2. Copy the `xiaomi_smart_bulb` direcotry within the `custom_components` directory of your homeassistant installation. 
The `custom_components` directory resides within your homeassistant configuration directory.
**Note**: if the custom_components directory does not exist, you need to create it.
After a correct installation, your configuration directory should look like the following.

    ```
    └── ...
    └── configuration.yaml
    └── custom_components
        └── xiaomi_smart_bulb
            └── __init__.py
            └── light.py
            └── manifest.json
     ```

### Configuration

Example configuration.yaml
```
light:
  - platform: xiaomi_smart_bulb
    name: OfficeLamp
    host: 192.168.0.101
    token: <token>
```
