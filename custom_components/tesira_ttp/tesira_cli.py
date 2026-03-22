# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\tesira_shell.py                                                              #
# Repository: tesira_ttp                                                                                               #
# Created Date: Sunday, March 22nd 2026, 11:00:09 PM                                                                   #
# Last Modified: Sunday, March 22nd 2026, 11:03:19 PM                                                                  #
# Original Author: Darnel Kumar                                                                                        #
# Author Github: https://github.com/Darnel-K                                                                           #
#                                                                                                                      #
# This code complies with: https://gist.github.com/Darnel-K/8badda0cabdabb15359350f7af911c90                           #
# Copyright (c) 2026 Darnel Kumar                                                                                      #
# #################################################################################################################### #
#!/usr/bin/env python3
"""
Tesira Interactive CLI
Usage:
    python3 tesira_cli.py --host 10.0.12.5 --proto ssh
"""

import asyncio
import argparse
from tesira_client import TesiraClient

# readline on Linux/Mac; dummy on Windows (optional enhancement below)
try:
    import readline
except ImportError:
    readline = None


BANNER = r"""
============================================================
               TESIRA INTERACTIVE TERMINAL
============================================================
Type any Tesira TTP command, e.g.:

    DEVICE get deviceInfo
    Level1 get level 1
    LogicState1 get states
    Level1 set level 1 -6.0
    SUBSCRIBE Level1 level 1 test 200
    unsubscribe test

Special commands:
    :exit       Quit CLI
    :json CMD   Run TesiraClient.json(CMD)
    :ping       Measure latency
============================================================
"""


async def subscription_printer(event: dict):
    """Print incoming publish-token events live."""
    print(f"\n[EVENT] {event}")
    print("TTP> ", end="", flush=True)


async def interactive_shell(client: TesiraClient):
    print(BANNER)

    # Attach subscription callback
    client._event_callback = subscription_printer

    loop = asyncio.get_event_loop()

    while True:
        # Run user input without blocking the event loop
        cmd = await loop.run_in_executor(None, lambda: input("TTP> ").strip())

        if not cmd:
            continue

        if cmd.lower() in (":exit", "exit", "quit"):
            print("Disconnecting...")
            await client.disconnect()
            print("Bye!")
            return

        if cmd.startswith(":json"):
            real_cmd = cmd[6:].strip()
            if not real_cmd:
                print("Usage: :json <TTP command>")
                continue

            try:
                result = await client.json(real_cmd)
                print(result)
            except Exception as e:
                print("ERROR:", e)
            continue

        if cmd == ":ping":
            try:
                ms = await client.ping()
                print(f"Ping: {ms:.2f} ms")
            except Exception as e:
                print("Ping ERROR:", e)
            continue

        # Normal TTP command
        try:
            result = await client.command(cmd)
            print(result)
        except Exception as e:
            print("ERROR:", e)


async def main():
    parser = argparse.ArgumentParser(description="Tesira Interactive CLI")
    parser.add_argument("--host", required=True, help="Tesira Host IP")
    parser.add_argument("--proto", default="ssh", choices=["ssh", "telnet"], help="Protocol")
    parser.add_argument("--user", default="default", help="Username")
    parser.add_argument("--password", default="", help="Password")
    parser.add_argument("--port", type=int, help="Port override", default=None)
    args = parser.parse_args()

    print(f"Connecting to {args.host} via {args.proto.upper()} ...")

    client = TesiraClient(
        host=args.host,
        username=args.user,
        password=args.password,
        port=args.port,
        proto=args.proto,
    )

    await client.connect()
    await interactive_shell(client)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting terminal.")
