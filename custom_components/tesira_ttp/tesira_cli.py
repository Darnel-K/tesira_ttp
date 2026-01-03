#!/usr/bin/env python3
"""Console test utility for TesiraTtpClient (Telnet).

Run on HAOS inside the Home Assistant Core container:

  ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 192.168.40.84 --tag volume --get
  ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 192.168.40.84 --tag volume --inc 1.0
  ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 192.168.40.84 --tag volume --set -20
  ha core exec python3 /config/custom_components/tesira_ttp/tesira_cli.py --host 192.168.40.84 --interactive
"""

import argparse
import asyncio

from tesira_client import TesiraTtpClient, parse_first_float

async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=23)
    ap.add_argument("--tag", default="volume")
    ap.add_argument("--ch", type=int, default=1)

    ap.add_argument("--get", action="store_true")
    ap.add_argument("--set", type=float)
    ap.add_argument("--inc", type=float)
    ap.add_argument("--raw", type=str)
    ap.add_argument("--interactive", action="store_true")

    args = ap.parse_args()

    c = TesiraTtpClient(args.host, args.port)

    async def send(line: str):
        resp = await c.send_and_wait(line, timeout=2.0)
        print(resp.strip())
        return resp

    if args.interactive:
        await c.connect()
        print("Connected. Type TTP commands; Ctrl-D to exit.")
        try:
            while True:
                line = await asyncio.get_running_loop().run_in_executor(None, lambda: input("> "))
                if not line.strip():
                    continue
                await send(line)
        except (EOFError, KeyboardInterrupt):
            pass
        await c.close()
        return 0

    if args.raw:
        await send(args.raw)
        await c.close()
        return 0

    tag, ch = args.tag, args.ch

    if args.get:
        resp = await send(f"{tag} get level {ch}")
        val = parse_first_float(resp)
        if val is not None:
            print(f"Parsed level: {val} dB")
        await c.close()
        return 0

    if args.set is not None:
        await send(f"{tag} set level {ch} {args.set:.3f}")
        await c.close()
        return 0

    if args.inc is not None:
        await send(f"{tag} increment level {ch} {args.inc:.3f}")
        await c.close()
        return 0

    ap.print_help()
    await c.close()
    return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
