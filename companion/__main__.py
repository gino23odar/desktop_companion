"""Command-line interface. Run from the repository root."""
import argparse
import json
import logging
from pathlib import Path
import sys

from .connection import connect, watch
from .discovery import list_ports
from .protocol import DeviceError, LinkError


def output(message):
    print(json.dumps(message, ensure_ascii=True), flush=True)


def event_output(message):
    # Events and diagnostic logs stay separate from command output.
    print(json.dumps(message, ensure_ascii=True), file=sys.stderr, flush=True)


def build_parser():
    parser = argparse.ArgumentParser(description="Desk Buddy USB companion")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--port", help="Explicit serial port, e.g. /dev/ttyUSB0 or COM3")
    selection.add_argument("--usb-serial", help="Select a CP210x bridge by USB serial number")
    parser.add_argument("--verbose", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("ports", "hello", "ping", "info", "boop", "get-mood", "reset-mood", "watch"):
        commands.add_parser(name)
    commands.add_parser("set-mood").add_argument("file", type=Path)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(message)s")
    client = None
    try:
        if args.command == "ports":
            for p in list_ports():
                output({"port": p.device, "description": p.description,
                        "vid": f"{p.vid:04X}" if p.vid is not None else None,
                        "pid": f"{p.pid:04X}" if p.pid is not None else None,
                        "usb_serial": p.serial_number})
            return 0
        options = dict(explicit=args.port, usb_serial=args.usb_serial,
                       on_event=event_output)
        if args.command == "watch":
            watch(**options)
            return 0
        payload = {}
        if args.command == "set-mood":
            with args.file.open(encoding="utf-8") as handle:
                mood = json.load(handle)
            if not isinstance(mood, dict):
                raise ValueError("Mood file must contain a JSON object, not a command envelope")
            payload["mood"] = mood
        client = connect(**options)
        command = {"info": "get_info"}.get(args.command, args.command.replace("-", "_"))
        reply = client.identity if command == "hello" else client.request(command, **payload)
        output(reply)
        return 0
    except KeyboardInterrupt:
        return 130
    except DeviceError as exc:
        event_output(exc.reply)
        return 2
    except (LinkError, OSError, ValueError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            try:
                client.close()
            except OSError:
                logging.warning("Could not close USB port cleanly")


if __name__ == "__main__":
    raise SystemExit(main())
