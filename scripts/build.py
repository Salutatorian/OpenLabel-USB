"""Build natively; macOS builds run on their matching GitHub Actions runners."""
import hashlib
import json
import importlib.metadata as metadata
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
licenses = root / 'licenses'
licenses.mkdir(exist_ok=True)
for name in ('Pillow', 'PyMuPDF', 'pyusb', 'pyinstaller'):
    distribution = metadata.distribution(name)
    for file in distribution.files or []:
        if 'license' in str(file).lower() or 'copying' in str(file).lower():
            source = Path(distribution.locate_file(file))
            if source.is_file():
                shutil.copy2(source, licenses / (name + '-' + source.name))
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
if python_license.is_file():
    shutil.copy2(python_license, licenses / 'Python-LICENSE.txt')
(licenses / 'BUILD_INFO.json').write_text(json.dumps({'python': sys.version, 'platform': platform.system(), 'architecture': platform.machine()}, indent=2))
if sys.platform == 'darwin':
    formula = json.loads(subprocess.check_output(['brew', 'info', '--json=v2', 'libusb'], text=True))['formulae'][0]
    (licenses / 'libusb-build.json').write_text(json.dumps({'version': formula['versions']['stable'], 'upstream_source': formula['urls']['stable']}, indent=2))
command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed',
           '--name', 'OpenLabel', '--collect-all', 'pymupdf', '--collect-submodules', 'usb',
           '--add-data', f'{licenses}:licenses', '--add-data', f'{root / "LICENSE"}:.',
           '--add-data', f'{root / "THIRD_PARTY.md"}:.']
is_mac = sys.platform == 'darwin'
if is_mac:
    prefix = subprocess.check_output(['brew', '--prefix', 'libusb'], text=True).strip()
    library = Path(prefix) / 'lib/libusb-1.0.dylib'
    command += ['--onedir', '--osx-bundle-identifier', 'io.github.salutatorian.openlabel',
                '--add-binary', f'{library.resolve()}:.']
else:
    command += ['--onefile']
command += [str(root / 'openlabel.py')]
subprocess.run(command, cwd=root, check=True)
assets = root / 'release-assets'
assets.mkdir(exist_ok=True)
if is_mac:
    app = root / 'dist/OpenLabel.app'
    executable = app / 'Contents/MacOS/OpenLabel'
    arch = 'arm64' if platform.machine() == 'arm64' else 'x64'
    actual = subprocess.check_output(['lipo', '-archs', str(executable)], text=True).strip()
    assert ('arm64' if arch == 'arm64' else 'x86_64') in actual, actual
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
    subprocess.run([str(executable), '--smoke-test'], check=True, timeout=60)
    output = assets / f'OpenLabel-macOS-{arch}.zip'
    subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(app), str(output)], check=True)
else:
    executable = root / 'dist/OpenLabel.exe'
    subprocess.run([str(executable), '--smoke-test'], check=True, timeout=60)
    shutil.copy2(executable, assets / 'OpenLabel-Windows-x64.exe')
print('Native build and packaged GUI smoke test passed.')
