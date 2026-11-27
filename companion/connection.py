"""Open and identify devices; maintain a connection in watch mode."""
import logging
import time

from .config import HEARTBEAT_INTERVAL, RECONNECT_DELAY
from .discovery import list_ports, select_port, open_port
from .protocol import LinkError, DeviceError
from .serial_client import SerialClient

LOG = logging.getLogger(__name__)


def connect(*, explicit=None, usb_serial=None, on_event=None,
            enumerate_ports=list_ports, opener=open_port):
    # Do not enumerate when the user explicitly supplied a port.
    device = select_port([] if explicit else enumerate_ports(), explicit, usb_serial)
    client = SerialClient(opener(device), on_event)
    try:
        client.handshake()
    except BaseException:
        try:
            client.close()
        except OSError:
            LOG.warning("Could not close USB port after handshake failure")
        raise
    LOG.info("Connected to Svinka on %s (firmware %s)", device,
             client.identity.get("firmware", "unknown"))
    return client


def watch(*, explicit=None, usb_serial=None, on_event=None,
          connector=connect, clock=time.monotonic, sleep=time.sleep,
          should_stop=lambda: False, heartbeat_interval=HEARTBEAT_INTERVAL,
          reconnect_delay=RECONNECT_DELAY):
    """Watch events and reconnect; never replay a mutating request."""
    while not should_stop():
        client = None
        try:
            client = connector(explicit=explicit, usb_serial=usb_serial,
                               on_event=on_event)
            next_ping = clock() + heartbeat_interval
            while not should_stop():
                client.poll(timeout=0.25)
                if clock() >= next_ping:
                    client.request("ping")
                    next_ping = clock() + heartbeat_interval
        except (LinkError, DeviceError, OSError) as exc:
            LOG.warning("Connection unavailable: %s", exc)
        finally:
            if client is not None:
                try:
                    client.close()
                except OSError:
                    LOG.warning("Could not close USB port cleanly")
        if not should_stop():
            sleep(reconnect_delay)
