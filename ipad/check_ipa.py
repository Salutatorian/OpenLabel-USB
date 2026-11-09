"""Validate the development IPA. Never labels an unsigned build install-ready."""
from pathlib import Path
import plistlib
import zipfile

files = list(Path('ipad/xtool').glob('*.ipa'))
assert len(files) == 1, files
with zipfile.ZipFile(files[0]) as bundle:
    plists = [n for n in bundle.namelist() if n.count('/') == 2 and n.endswith('.app/Info.plist')]
    assert len(plists) == 1, plists
    info = plistlib.loads(bundle.read(plists[0]))
    assert info['CFBundleIdentifier'] == 'io.github.salutatorian.openlabel.ipad', info
    assert 2 in info['UIDeviceFamily'], info
    executable = plists[0].removesuffix('Info.plist') + info['CFBundleExecutable']
    assert bundle.getinfo(executable).file_size > 0
print('Unsigned development IPA contains the iPad app. Signing and device installation are still required.')
