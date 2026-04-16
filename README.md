
# Tesira Text Protocol (SSH & Telnet) Integration for Home Assistant

![GitHub License](https://img.shields.io/github/license/Darnel-K/tesira_ttp)
![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange)
![Platform](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue)
![Protocol](https://img.shields.io/badge/Protocol-TTP%20(SSH)-lightgrey)
![Protocol](https://img.shields.io/badge/Protocol-TTP%20(Telnet)-lightgrey)

![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/Darnel-K/tesira_ttp)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr/Darnel-K/tesira_ttp)
![GitHub Release](https://img.shields.io/github/v/release/Darnel-K/tesira_ttp)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/Darnel-K/tesira_ttp/total)
![GitHub release (latest by SemVer)](https://img.shields.io/github/downloads/Darnel-K/tesira_ttp/latest/total)

This Home Assistant integration provides control of **Biamp Tesira** systems using the **Tesira Text Protocol (TTP)** over **Telnet (TCP/23)** and **SSH (TCP/22)**.

> ⚠️ **WORK IN PROGRESS**
> This project is currently under active development. Features may be incomplete or subject to change.

## Requirements

- A Tesira DSP with **Telnet (TCP/23)** or **SSH (TCP/22)** enabled
- Network access from Home Assistant to the Tesira DSP

## Installation

### HACS

1. Open **HACS → Integrations**
2. Select **⋮ → Custom repositories**
3. Add `https://github.com/Darnel-K/tesira_ttp` as **Integration**
4. Install and restart Home Assistant

### Manual

Copy:

`custom_components/tesira_ttp/`

into:

`/config/custom_components/tesira_ttp/`

then restart Home Assistant.

## Configuration

After installation, configure from:

**Settings → Devices & services → Add integration → Tesira Text Protocol (SSH & Telnet)**

### 1. Create Integration (Hub + First Device)

When you add the integration, you will be prompted for:

1. **Hub title**
2. **Host** (Tesira IP or hostname)
3. **Port**
4. **Protocol** (`ssh` or `telnet`)
5. **Username** (SSH only)
6. **Password** (SSH only)

Notes:

- Default connection values are SSH on port `22`, user `default`, blank password.
- Telnet authentication is intentionally restricted to user `default` with blank password.
- Connectivity and device info are validated before the device is saved.

### 2. Configure Devices (Add/Edit/Remove/Primary)

Device management is available in the **reconfiguration flow** for an existing integration:

1. Open the integration card.
2. Next to your hub select **⋮ → Reconfigure**.
3. Choose **Configure Devices**.

Available actions:

- **Add Device**: Add another Tesira endpoint to the same hub.
- **Edit Device**: Update host/port/protocol/credentials for an existing configured device.
- **Remove Device**: Remove a device.
- **Change Primary Device**: Select which configured device is used as the hub connection source.

Important behavior:

- You cannot remove the current primary device until another device is set as primary.
- Editing a device must resolve to the same physical Tesira device identity.

### 3. Configure Entities (Add/Edit/Remove)

To add or manage entities:

1. Open the integration card.
2. Next to your hub select **Settings Cog**.

Entity management actions:

- **Add Entity**: Create a new entity from a selected block type.
- **Edit Entity**: Modify an existing entity definition.
- **Remove Entity**: Remove one or more entities.

#### How Entity Live Updates Work

- If **Enable Live Updates** is ON, the entity uses Tesira subscriptions for near real-time state changes.
- If OFF, the entity uses polling updates.

## Debugging

Enable debug logs in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.tesira_ttp: debug
```

## Development / CLI Testing

An interactive CLI for testing Tesira Text Protocol commands is included:

`custom_components/tesira_ttp/tesira_cli.py`

It provides a cross‑platform interactive shell (powered by `prompt_toolkit`)
for sending Tesira Text Protocol commands, receiving real‑time publish‑token event updates,
and testing SSH or Telnet connectivity directly from the terminal.

---

### CLI Arguments

```text
--host <IP>         (Required) Tesira device IP address
--proto <proto>     Protocol: "ssh" (default) or "telnet"
--user <username>   Username (default: "default")
--password <pass>   Password (default: blank)
--port <port>       Override TCP port (defaults: SSH=22, Telnet=23)
```

### Connection Examples from HA Core on HAOS

Below are example commands demonstrating different connection scenarios.

#### Connect with SSH (default protocol)

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 10.xxx.xxx.xxx
```

or

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 10.xxx.xxx.xxx --proto ssh
```

You do not need to specify '`--proto ssh`' when connecting with SSH

#### Connect with non-default port (SSH)

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 10.xxx.xxx.xxx --port 2222
```

#### Connect with username and blank password (SSH)

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 10.xxx.xxx.xxx --user admin
```

#### Connect with username and password (SSH)

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 10.xxx.xxx.xxx --user admin --password MySecretPass
```

#### Connect with non-default port, username and password (SSH)

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 10.xxx.xxx.xxx --port 2222 --user admin --password MySecretPass
```

#### Connect with Telnet

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 10.xxx.xxx.xxx --proto telnet
```

#### Connect with non-default port (Telnet)

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 10.xxx.xxx.xxx --proto telnet --port 2323
```

### Command Examples

After launching, you can enter commands such as:

```text
DEVICE get deviceInfo
Level1 get level 1
Level1 subscribe level 1 test1 100
unsubscribe test1
```

Special commands include:

```text
:json <command>   → run a command and parse Tesira-style JSON
:ping             → measure round‑trip latency
:exit             → quit the CLI
```

## Supported Blocks and Entities

| Block Type | Home Assistant Platform | Main Features |
| ---------- | ----------------------- | ------------- |
| `level` | `media_player` | Set volume, step volume, mute/unmute |
| `logic_state` | `switch` | On/Off, toggle |

Additional entities created automatically:

- Hub connection status binary sensor
- Per-device network reachability binary sensor

## Acknowledgements

This project is a complete rewrite, but it began as a fork of the original Tesira TTP integration created by **bxthomas**. The original repository can be found here:

**<https://github.com/bxthomas/tesira_ttp>**

Their work provided the initial foundation that inspired this redesigned and fully expanded version.

## License

Released under the **GNU Affero General Public License v3.0 (AGPL‑3.0)**.

## Status

| Master | Staging | Develop |
| ------ | ------- | ------- |
| ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Darnel-K/tesira_ttp/ci.yml?branch=master&label=HACS%20-%20Hassfest) | ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Darnel-K/tesira_ttp/ci.yml?branch=staging&label=HACS%20-%20Hassfest) | ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Darnel-K/tesira_ttp/ci.yml?branch=develop&label=HACS%20-%20Hassfest) |
| ![GitHub manifest version (branch)](https://img.shields.io/github/manifest-json/v/Darnel-K/tesira_ttp/master?filename=custom_components%2Ftesira_ttp%2Fmanifest.json&label=Version) | ![GitHub manifest version (branch)](https://img.shields.io/github/manifest-json/v/Darnel-K/tesira_ttp/staging?filename=custom_components%2Ftesira_ttp%2Fmanifest.json&label=Version) | ![GitHub manifest version (branch)](https://img.shields.io/github/manifest-json/v/Darnel-K/tesira_ttp/develop?filename=custom_components%2Ftesira_ttp%2Fmanifest.json&label=Version) |
| ![GitHub Release](https://img.shields.io/github/v/release/Darnel-K/tesira_ttp) |  | ![GitHub Release](https://img.shields.io/github/v/release/Darnel-K/tesira_ttp?include_prereleases) |
