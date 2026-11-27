# Desk Buddy companion (PR-06)

## Requirements

- Python 3.10 or newer; CI uses 3.12.
- pySerial 3.5.
- ESP32 running firmware 0.5.0 (USB protocol v1).
- A USB data cable. Wi-Fi and Bluetooth on the ESP32 are not required.
- Close Arduino Serial Monitor before connecting the companion.

From the repository root on Ubuntu:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r companion/requirements.txt
python -m companion ports
```

On Windows (PowerShell), without changing execution policy:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r companion/requirements.txt
.\.venv\Scripts\python.exe -m companion ports
```

## Commands

```bash
python -m companion hello
python -m companion ping
python -m companion info
python -m companion get-mood
python -m companion boop
python -m companion set-mood moods/sleepy.json
python -m companion set-mood moods/missing_you.json
python -m companion reset-mood
python -m companion watch
```

The mood file contains the mood object, not an entire set_mood command.
Specify a port if discovery is ambiguous or the USB bridge is not CP210x:

```bash
python -m companion --port /dev/ttyUSB0 info
python -m companion --port COM3 watch
python -m companion --usb-serial YOUR_BRIDGE_SERIAL watch
```

Options go before the subcommand. A single CP210x bridge (10C4:EA60)
is automatically selected. If multiple match, the user must select one.
The hello handshake checks the device name and protocol; it is not
cryptographic authentication. The target firmware version is 0.5.0;
older firmware may identify itself but lack later commands.

## Protocol behavior

- 115200 baud, 8N1, no hardware/software flow control.
- Compact newline-delimited JSON, maximum 511 bytes per outgoing line
  excluding the LF. Incoming lines are bounded at 4096 bytes.
- One request in flight at a time; responses correlated by request_id.
- Unsolicited ready and event messages are delivered separately.
- Ignore non-JSON boot logs and malformed lines. Partial lines survive
  read timeouts.
- Default reply timeout: two seconds after the write completes, plus
  possible serial read timeout granularity. Write timeout: one second.
- The hello handshake retries up to three times because opening a USB
  serial port can reset the ESP32. No mutating command is automatically
  retried: if a reply is lost, the outcome is unknown. Use get-mood to
  check state before retrying a mood update.
- In watch mode, ping every three seconds while connected. On errors,
  close the serial port, wait two seconds, then discover and handshake
  again. The explicit port option always uses the same named port.
- Watch mode is event monitoring only in PR-06. Stop it before running
  another command or opening Arduino Serial Monitor.
- A command prints the JSON response to stdout. Events and logs go to
  stderr. Exit codes: 0 success, 1 local/connection/protocol error,
  2 device rejection, 130 keyboard interrupt.

## Native tests

```bash
python -m unittest discover -s tests/companion -v
python -m compileall -q companion
```

The simulated transport does not require pySerial or hardware. CI also
installs pySerial and checks port enumeration on Windows and Linux.
The simulated device tests do not prove physical USB behavior.

## Manual acceptance tests

1. Connect firmware 0.5.0 and run ports, hello, info, and ping.
2. Send both supplied mood files and verify the rendered character.
3. Read the current mood; compare with the sent definition.
4. Run boop and confirm a temporary reaction. Run watch separately,
   tap the display and verify an event with source touch.
5. With watch running, disconnect USB and reconnect. Confirm a new
   handshake and another physical-touch event. Try starting watch
   with the device unplugged as well.
6. Stop watch. Reconnect power and verify the last mood survives.
7. Send an invalid mood (e.g. eyes laser); confirm a device error and
   unchanged active mood. Run reset-mood and verify persistence.
8. Test on Windows before deploying to the recipient's computer.

## Limitations

Only one program can own the serial connection at a time. There is no
internet sync, automatic startup, GUI, installer, multi-device support,
or persistent event queue yet. Opening the port may cause a board reset
depending on the USB bridge and driver. Events can be lost while no client
is connected. A failed request does not prove it was not executed.
