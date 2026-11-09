"""Experimental macOS transport using PyUSB and bundled libusb.

No firmware writes or vendor software are involved. Hardware validation is pending.
"""
from pathlib import Path
import sys
from device_profile import VID, PID, matches_model

def backend():
    import usb.backend.libusb1
    bundle = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
    libraries = list(bundle.glob('libusb-1.0*.dylib'))
    if libraries:
        result = usb.backend.libusb1.get_backend(find_library=lambda _: str(libraries[0]))
    else:
        result = usb.backend.libusb1.get_backend()
    if result is None:
        raise OSError('USB library unavailable. Use the packaged Mac app or install libusb for source builds.')
    return result

def _key(dev):
    return f'usb:{dev.bus}:{dev.address}'

def devices():
    import usb.core
    import usb.util
    found = []
    for dev in usb.core.find(find_all=True, idVendor=VID, idProduct=PID, backend=backend()):
        try:
            if matches_model(dev.idVendor, dev.idProduct, dev.product or ''):
                found.append(_key(dev))
        finally:
            usb.util.dispose_resources(dev)
    return found

def _bulk_output(configuration):
    import usb.util
    for interface in configuration:
        if interface.bInterfaceClass != 7 or interface.bAlternateSetting != 0:
            continue
        for endpoint in interface:
            if (usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT
                    and usb.util.endpoint_type(endpoint.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK):
                return interface.bInterfaceNumber, endpoint.bEndpointAddress
    raise OSError('Printer does not expose a supported printer-class bulk OUT interface.')

def send_raw(path, payload):
    import usb.core
    import usb.util
    from usb_print import write_all
    for dev in usb.core.find(find_all=True, idVendor=VID, idProduct=PID, backend=backend()):
        claimed = False
        number = None
        try:
            if _key(dev) != path or not matches_model(dev.idVendor, dev.idProduct, dev.product or ''):
                continue
            try:
                config = dev.get_active_configuration()
            except usb.core.USBError:
                dev.set_configuration()
                config = dev.get_active_configuration()
            number, endpoint = _bulk_output(config)
            usb.util.claim_interface(dev, number)
            claimed = True
            return write_all(payload, lambda chunk: int(dev.write(endpoint, chunk, timeout=10000)))
        except usb.core.USBError as exc:
            raise OSError('USB transfer failed. Close other printing apps and check USB access. '
                          'If any bytes were sent, check the printer before retrying. ' + str(exc)) from exc
        finally:
            if claimed:
                usb.util.release_interface(dev, number)
            usb.util.dispose_resources(dev)
    raise OSError('Printer disconnected. Reconnect it and refresh printers.')
