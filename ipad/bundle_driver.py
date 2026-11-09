"""Embed the compiled DEXT for a signing-capable development team.

This does not sign, provision, or bypass iPadOS security.
"""
from pathlib import Path
import plistlib
import shutil
import tempfile
import zipfile
import struct

root = Path(__file__).resolve().parent
ipas = list((root / 'xtool').glob('*.ipa'))
dexts = list((root / 'Driver/build/Build/Products').glob('**/*.dext'))
assert len(ipas) == len(dexts) == 1, (ipas,dexts)
driver = dexts[0]
info = plistlib.loads((driver / 'Info.plist').read_bytes())
binary = (driver / info['CFBundleExecutable']).read_bytes()
magic,cpu = struct.unpack_from('<II',binary)
assert magic == 0xfeedfacf and cpu == 0x100000c, 'Expected ARM64 DEXT'
commands = struct.unpack_from('<I',binary,16)[0]
offset = 32
driverkit = False
for _ in range(commands):
    command,size = struct.unpack_from('<II',binary,offset)
    assert size >= 8 and offset+size <= len(binary)
    if command == 0x32:
        driverkit = struct.unpack_from('<I',binary,offset+8)[0] == 10
    offset += size
assert driverkit, 'Expected DriverKit Mach-O platform'
output = root / 'driver-artifacts'
output.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as temporary:
    staging = Path(temporary)
    with zipfile.ZipFile(ipas[0]) as source:
        for name in source.namelist():
            assert not name.startswith('/') and '..' not in Path(name).parts
        source.extractall(staging)
    apps = list((staging / 'Payload').glob('*.app'))
    assert len(apps) == 1
    destination = apps[0] / 'Library/SystemExtensions' / (info['CFBundleIdentifier']+'.dext')
    shutil.copytree(driver,destination)
    # Include templates for the team doing real codesigning; these are not grants.
    shutil.copy2(root/'USBApp.entitlements',output/'USBApp.entitlements')
    shutil.copy2(root/'Driver/Driver.entitlements',output/'Driver.entitlements')
    with zipfile.ZipFile(output/'OpenLabeliPad-USB-UNSIGNED.ipa','w',zipfile.ZIP_DEFLATED) as archive:
        for file in staging.rglob('*'):
            if file.is_file():
                archive.write(file,file.relative_to(staging).as_posix())
(output/'READ-BEFORE-INSTALL.txt').write_text(
    'UNSIGNED DRIVER DEVELOPMENT BUILD. It is not install-ready.\n'
    'Contains an ARM64 DriverKit extension and native iPad app, compiled without device provisioning.\n'
    'A signing-capable developer team must supply matching app/DriverKit profiles, certificates and entitlements.\n'
    'Normal free-account sideloading does not supply these. No physical iPad USB print has been verified.\n'
    'See ipad/Driver/README.md in the source repository.\n')
print('Verified ARM64 DriverKit binary and embedded it. Device provisioning and physical testing are still required.')
