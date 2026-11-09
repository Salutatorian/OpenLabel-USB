"""Platform-selected USB transport and bounded partial-write handling."""
import sys

def write_all(payload, writer):
    offset = 0
    while offset < len(payload):
        chunk = payload[offset:offset + 65536]
        count = writer(chunk)
        if not isinstance(count, int) or not 0 < count <= len(chunk):
            raise OSError('USB transfer made no valid progress. Do not retry until you check the printer.')
        offset += count
    return offset


def devices():
    if sys.platform == 'win32':
        from windows_usb import devices as discover
    elif sys.platform == 'darwin':
        from mac_usb import devices as discover
    else:
        raise OSError('This build supports Windows and macOS only.')
    return discover()

def send_raw(path, payload):
    if sys.platform == 'win32':
        from windows_usb import send_raw as send
    elif sys.platform == 'darwin':
        from mac_usb import send_raw as send
    else:
        raise OSError('This build supports Windows and macOS only.')
    return send(path, payload)
