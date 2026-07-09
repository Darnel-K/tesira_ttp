#!/usr/bin/env python3
"""Tesira Interactive CLI using prompt_toolkit (Windows/Linux/Mac Compatible)."""

import argparse
import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

try:
    from .client import TesiraClient
except ImportError:
    # Support direct execution: python .\custom_components\tesira_ttp\tesira_client\cli.py
    from client import TesiraClient


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


async def subscription_printer(event: dict, session: PromptSession):
    # Print event above the input line
    print(f"[EVENT] {event}")

    # Safely request a prompt redraw
    app = session.app
    if app is not None:
        app.invalidate()


async def interactive_shell(client: TesiraClient):
    print(BANNER)

    # Prompt toolkit session (handles async-safe input line)
    session = PromptSession("TTP> ")

    # Assign global callback (wrapped so we can access session)
    async def printer(event):
        await subscription_printer(event, session)

    client._event_callback = printer

    # Keep terminal safe while async printing occurs
    with patch_stdout():
        while True:
            try:
                cmd = await session.prompt_async()
            except (EOFError, KeyboardInterrupt):
                print("Exiting.")
                break

            cmd = cmd.strip()
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
    parser.add_argument("--host", required=True, help="Tesira Host")
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
        print("\nExiting.")
