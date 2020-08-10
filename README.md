# xiaomi_smart_bulb
Xiaomi Smart Bulb (MJDPL01YL) Home Assistant integration

### Token
The integration needs the token of the light, the can be obtained by this methods:
https://github.com/Maxmudjon/com.xiaomi-miio/blob/master/docs/obtain_token.md

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
    name: DolgozoLampa
    host: 192.168.0.101
    token: <token>
```
