
# Tesira TTP Control Integration for Home Assistant

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

This Home Assistant integration provides comprehensive control of **Biamp Tesira** systems using the **Tesira Text Protocol (TTP)** over **Telnet (TCP/23)** & **SSH (TCP/22)**. It exposes a **range of entity types**, enabling full interaction with Tesira DSP blocks directly from Home Assistant.

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

Navigate to: **Settings → Devices & services → Add integration → Tesira TTP Control (Telnet)**.

## Debugging

Enable debug logs in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.tesira_ttp: debug
```

## Development / CLI Testing

A TTP command-line tester is included:

```
custom_components/tesira_ttp/tesira_cli.py
```

Example usage from HA Core on HAOS:

```bash
ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --ip 192.168.40.84 --tag volume --get
```

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
