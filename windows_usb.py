"""Direct Windows USB printer-class transport. No spooler or vendor DLLs."""
import ctypes as c
from ctypes import wintypes as w
import uuid
from device_profile import matches_model

class GUID(c.Structure):
    _fields_ = [('bytes', c.c_ubyte * 16)]

class PropertyKey(c.Structure):
    _fields_ = [('guid', GUID), ('pid', w.DWORD)]

class DevInfo(c.Structure):
    _fields_ = [('size', w.DWORD), ('guid', GUID), ('devinst', w.DWORD), ('reserved', c.c_size_t)]

class Interface(c.Structure):
    _fields_ = [('size', w.DWORD), ('guid', GUID), ('flags', w.DWORD), ('reserved', c.c_size_t)]

def devices():
    api = c.WinDLL('setupapi', use_last_error=True)
    guid = GUID((c.c_ubyte * 16).from_buffer_copy(uuid.UUID('28d78fad-5a12-11d1-ae5b-0000f803a8c2').bytes_le))
    api.SetupDiGetClassDevsW.argtypes = [c.POINTER(GUID), w.LPCWSTR, w.HWND, w.DWORD]
    api.SetupDiGetClassDevsW.restype = w.HANDLE
    api.SetupDiEnumDeviceInterfaces.argtypes = [w.HANDLE, c.c_void_p, c.POINTER(GUID), w.DWORD, c.POINTER(Interface)]
    api.SetupDiGetDeviceInterfaceDetailW.argtypes = [w.HANDLE, c.POINTER(Interface), c.c_void_p, w.DWORD, c.POINTER(w.DWORD), c.c_void_p]
    api.SetupDiDestroyDeviceInfoList.argtypes = [w.HANDLE]
    api.SetupDiGetDeviceRegistryPropertyW.argtypes = [w.HANDLE, c.POINTER(DevInfo), w.DWORD, c.POINTER(w.DWORD), c.c_void_p, w.DWORD, c.POINTER(w.DWORD)]
    api.SetupDiGetDevicePropertyW.argtypes = [w.HANDLE, c.POINTER(DevInfo), c.POINTER(PropertyKey), c.POINTER(w.DWORD), c.c_void_p, w.DWORD, c.POINTER(w.DWORD), w.DWORD]
    key = PropertyKey(GUID((c.c_ubyte * 16).from_buffer_copy(uuid.UUID('540b947e-8b40-45bc-a8a2-6a0b894cbda2').bytes_le)), 4)
    handle = api.SetupDiGetClassDevsW(c.byref(guid), None, None, 0x12)
    if handle == c.c_void_p(-1).value:
        raise c.WinError(c.get_last_error())
    found = []
    try:
        index = 0
        while True:
            item = Interface(); item.size = c.sizeof(item)
            if not api.SetupDiEnumDeviceInterfaces(handle, None, c.byref(guid), index, c.byref(item)):
                error = c.get_last_error()
                if error == 259: break
                raise c.WinError(error)
            needed = w.DWORD()
            api.SetupDiGetDeviceInterfaceDetailW(handle, c.byref(item), None, 0, c.byref(needed), None)
            if not needed.value: raise c.WinError(c.get_last_error())
            buf = c.create_string_buffer(needed.value)
            c.cast(buf, c.POINTER(w.DWORD))[0] = 8 if c.sizeof(c.c_void_p) == 8 else 6
            info = DevInfo(); info.size = c.sizeof(info)
            if not api.SetupDiGetDeviceInterfaceDetailW(handle, c.byref(item), buf, needed, None, c.byref(info)):
                raise c.WinError(c.get_last_error())
            path = c.wstring_at(c.addressof(buf) + 4)
            # Restrict discovery to this model, not arbitrary USB printers.
            if 'vid_0fe6&pid_811e' in path.lower():
                description = c.create_unicode_buffer(1024)
                prop_type = w.DWORD()
                ok = api.SetupDiGetDevicePropertyW(handle, c.byref(info), c.byref(key), c.byref(prop_type), description, c.sizeof(description), None, 0)
                if not ok:
                    ok = api.SetupDiGetDeviceRegistryPropertyW(handle, c.byref(info), 14, None, description, c.sizeof(description), None)
                if ok and matches_model(0x0FE6, 0x811E, description.value): found.append(path)
            index += 1
        return found
    finally:
        api.SetupDiDestroyDeviceInfoList(handle)

def _open(path):
    # Revalidate against currently enumerated devices before opening a device path.
    if path not in devices(): raise OSError('Printer disconnected. Reconnect it and refresh printers.')
    api = c.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, c.c_void_p, w.DWORD, w.DWORD, w.HANDLE]
    api.CreateFileW.restype = w.HANDLE
    api.CloseHandle.argtypes = [w.HANDLE]
    api.WriteFile.argtypes = [w.HANDLE, c.c_void_p, w.DWORD, c.POINTER(w.DWORD), c.c_void_p]
    handle = api.CreateFileW(path, 0x40000000, 3, None, 3, 0, None)
    if handle == c.c_void_p(-1).value: raise c.WinError(c.get_last_error())
    return api, handle

def probe(path):
    """Open and close the USB interface without sending any bytes."""
    api, handle = _open(path)
    api.CloseHandle(handle)

def send_raw(path, payload):
    from usb_print import write_all
    api, handle = _open(path)
    try:
        def write(chunk):
            buf = c.create_string_buffer(chunk)
            count = w.DWORD()
            if not api.WriteFile(handle, buf, len(chunk), c.byref(count), None):
                raise c.WinError(c.get_last_error())
            return count.value
        return write_all(payload, write)
    finally:
        api.CloseHandle(handle)
