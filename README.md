# xiaomi_smart_bulb
Xiaomi Smart Bulb (MJDPL01YL) Home Assistant integration

This is a custom components to Home Assistant, which handles Xiaomi Smart Bulb (MJDPL01YL).

Token
The integration needs the token of the light, the can be obtained by this methods:
https://github.com/Maxmudjon/com.xiaomi-miio/blob/master/docs/obtain_token.md

Configuration

Example configuration.yaml
<code>
light:
  - platform: xiaomi_smart_bulb
    name: DolgozoLampa
    host: 192.168.0.101
    token: <token>
</code>
