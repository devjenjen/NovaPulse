# SteelSeries GG Engine Local API

NovaPulse relies on the undocumented local web server spawned by the SteelSeries GG Engine. This document outlines how we interact with it.

## 1. Finding the Server
The GG Engine writes a JSON file containing the server's current address to:
`%PROGRAMDATA%\SteelSeries\SteelSeries Engine 3\coreProps.json`

Example content:
```json
{
  "address": "127.0.0.1:49152",
  "encryptedAddress": "127.0.0.1:49153"
}
```
NovaPulse parses this file at startup to locate the active port.

## 2. Battery Polling Endpoint
To get the battery status, we query the undocumented endpoint:
`GET https://{encryptedAddress}/subApps/battery/`

### Response Format
The server returns an array of devices. We look for the "Arctis Nova Pro Wireless" device.

```json
[
  {
    "name": "Arctis Nova Pro Wireless",
    "batteryLevel": 85,
    "batteryStatus": "discharging",
    "charging": false,
    "transmitter": {
      "name": "Transmitter",
      "batteryLevel": 100,
      "charging": true
    }
  }
]
```

**Key Fields:**
- `batteryLevel`: Headset battery (0-100). If the headset is off, this is usually 0 and `charging` is false, which can trigger false positives. NovaPulse implements state checks to verify it is actually online.
- `transmitter.batteryLevel`: The spare battery docked in the base station.

## 3. GameSense API (OLED Integration)
To flash messages on the base station's OLED screen, we register a dummy "game" and send events.

**Registration:** `POST https://{encryptedAddress}/game_metadata`
Payload:
```json
{
  "game": "NOVA_PULSE",
  "game_display_name": "NovaPulse System",
  "developer": "NovaPulse"
}
```

**Sending an Event:** `POST https://{encryptedAddress}/game_event`
Payload:
```json
{
  "game": "NOVA_PULSE",
  "event": "BATTERY_CRITICAL",
  "data": {
    "value": 1
  }
}
```
*(Note: A corresponding binding must be registered beforehand using the `/bind_game_event` endpoint to map `BATTERY_CRITICAL` to a specific OLED layout).*

## SSL/TLS Notes
The GG Engine uses a self-signed certificate for the `encryptedAddress`. Therefore, all HTTP requests must disable SSL verification (`verify=False` in Python `requests`), which requires suppressing the `InsecureRequestWarning`.
