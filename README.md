# Tesira TTP Volume (Home Assistant)

A Home Assistant custom integration that exposes **Biamp Tesira** level controls as `media_player` entities
using the **Tesira Text Protocol (TTP)** over **Telnet (TCP/23)**.

## Features

- UI setup via **Config Flow**
- Add **multiple controls** (instance tag + channel) under one Tesira device via **Options**
- `media_player` entity with:
  - volume slider (maps 0–100% to your chosen dB range)
  - volume up/down (relative step dB)
  - mute (best-effort; depends on block)

## Requirements

- Tesira Text Protocol server enabled (Telnet / port 23)
- Home Assistant with network access to the Tesira device

## Install

### HACS (Custom repository)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/bxthomas/tesira_ttp` as **Integration**
3. Install, then restart Home Assistant

### Manual

Copy `custom_components/tesira_ttp/` to `/config/custom_components/tesira_ttp/` and restart HA.

## Setup

Settings → Devices & services → Add integration → **Tesira TTP Volume (Telnet)**

- ip / Port
- Add your first control (name, instance tag, channel, min/max dB, step dB)

To add more controls later:

- Open the integration → **Configure** → Add / Edit / Remove controls

## Troubleshooting

Enable debug logs:

```yaml
logger:
  default: info
  logs:
    custom_components.tesira_ttp: debug
```

## Development / CLI smoke test

A small helper is included:

`custom_components/tesira_ttp/tesira_cli.py`

Run inside HA Core container on HAOS:

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --ip 192.168.40.84 --tag volume --get
```
