# Third-party software and corresponding source

OpenLabel public releases: AGPL-3.0-only. Copyright 2026 OpenLabel contributors. Complete application source and build scripts are in this repository at each release tag and through GitHub's source ZIP/tarball links beside binary assets.

Dependencies retain their licenses. The build script copies their shipped notices into the app's `licenses` resources. Source distributions and build information for pinned dependencies are available here:

| Component | Version | License | Corresponding source / build information |
| --- | --- | --- | --- |
| Pillow | 12.2.0 | HPND and bundled notices | https://pypi.org/project/pillow/12.2.0/#files ; https://github.com/python-pillow/Pillow |
| PyMuPDF | 1.28.2 | AGPL-3.0 or commercial; this project uses AGPL | https://pypi.org/project/PyMuPDF/1.28.2/#files ; https://github.com/pymupdf/PyMuPDF |
| MuPDF inside PyMuPDF | 1.28.2 | AGPL-3.0 | https://github.com/ArtifexSoftware/mupdf/tree/1.28.2 ; https://mupdf.com/releases/ |
| PyUSB | 1.3.1 | BSD-3-Clause | https://pypi.org/project/pyusb/1.3.1/#files ; https://github.com/pyusb/pyusb |
| libusb, Mac only | Recorded in bundled `libusb-build.json` | LGPL-2.1-or-later | Exact upstream source URL/hash recorded in that JSON; https://github.com/libusb/libusb |
| Python | CI-selected 3.12 patch | PSF and bundled notices | https://www.python.org/downloads/source/ ; https://github.com/python/cpython/tree/3.12 |
| Tcl/Tk | Bundled with selected Python | BSD-style notices | https://www.tcl.tk/software/tcltk/download.html |
| PyInstaller bootloader | 6.22.3 | GPL-2.0-or-later with bootloader exception | https://pypi.org/project/pyinstaller/6.22.3/#files ; https://github.com/pyinstaller/pyinstaller |

On PyPI, select the **source distribution**, not a binary wheel. These upstream sources and the checked-in build workflow document the components combined into releases. Upstream distributions can contain further components with their own notices. PyInstaller's exception permits bundling; it does not change OpenLabel's AGPL license.

The Mac libusb dylib is dynamically linked and unmodified. It can be replaced with an ABI-compatible build; modifying the app bundle can require repeating local ad-hoc signing. Use its recorded upstream source and standard libusb build instructions.

REA (MIT) was used during investigation, not bundled at runtime: https://github.com/morluto/rea . Supplementary pefile, pyelftools and Capstone analysis tools are not runtime dependencies. The project owner supplied the screenshot. OS fonts are selected at runtime and not redistributed.
