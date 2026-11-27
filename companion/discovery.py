"""Choose a USB serial port conservatively; verify identity separately"""
from .config import USB_BRIDGES, BAUD_RATE, READ_TIMEOUT, WRITE_TIMEOUT
from .protocol import LinkError


def list_ports():
    from serial.tools import list_ports
    return sorted(list_ports.comports(), key=lambda port: port.device)


def select_port(ports, explicit=None, usb_serial=None):
    if explicit:
        return explicit
    candidates = [p for p in ports if (p.vid, p.pid) in USB_BRIDGES
                  and (usb_serial is None or p.serial_number == usb_serial)]
    if not candidates:
        raise LinkError("No matching CP210x port; use ports and --port to select it")
    if len(candidates) > 1:
        raise LinkError("Multiple matching ports; use --port or --usb-serial")
    return candidates[0].device


def open_port(device):
    import serial
    port = serial.Serial(port=None, baudrate=BAUD_RATE,
                         timeout=READ_TIMEOUT, write_timeout=WRITE_TIMEOUT,
                         rtscts=False, dsrdtr=False, xonxoff=False)
    # Set desired control-line states before opening. Some drivers may
    # still briefly toggle these lines, resetting the ESP32
    port.dtr = False
    port.rts = False
    port.port = device
    try:
        port.open()
    except OSError:
        port.close()
        raise
    return port
