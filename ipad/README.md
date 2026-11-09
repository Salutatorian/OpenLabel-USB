# OpenLabel for iPad — xtool development build

**This is a label-editor/encoder preview, not a USB-printing release.** It builds with [xtool 1.24.0](https://github.com/xtool-org/xtool/releases/tag/1.24.0). The desktop releases remain separate.

## What is implemented

- Native SwiftUI iPad interface, portrait and landscape.
- Fixed 4 x 6 stock, live text preview, image and first-page PDF import from Files.
- Independent Swift TSPL encoder matching the tested Windows byte format.
- Export/share PNG and raw `.prn` files.

## What is not implemented or validated

No USBDriverKit extension is embedded. **There is no working direct USB print button.** Nothing has been signed for or installed on a physical iPad, and iPad output has not been physically printed. Exporting a `.prn` file does not itself print it.

## Why xtool helps, and where it stops

xtool supports app building/signing/installation on Windows through WSL. Its current packager models applications and ordinary `.appex` extensions, not DriverKit `.dext` products. A regular/free Apple ID can provision ordinary apps subject to Apple's limits; it does not supply the DriverKit provisioning needed for this printer connection. A paid account alone does not mean all required USB entitlements have been approved.

The remaining direct-USB work requires an M-series iPad, a DriverKit-enabled app ID/profile with the required USB transport permissions, an actual driver extension, compatible packaging/signing, and physical testing. It must match the MHT-L1081 (`0FE6:811E`), discover its printer-class bulk OUT endpoint, expose a bounded user-client write interface, and deliver the exact label bytes. No vendor firmware or driver binary should be reused.

References:

- [xtool Windows/WSL setup](https://github.com/xtool-org/xtool/blob/main/Documentation/xtool.docc/Installation-Linux.md)
- [xtool packager product types](https://github.com/xtool-org/xtool/blob/main/Sources/PackLib/Planner.swift)
- [Apple DriverKit provisioning](https://developer.apple.com/help/account/provisioning-profiles/create-a-driverkit-development-provisioning-profile)
- [Apple iPad DriverKit requirements](https://developer.apple.com/documentation/driverkit/creating-drivers-for-ipados)

## Build

The GitHub workflow `iPad xtool development` builds from the `ipad-xtool` branch. It tests the encoder on a Mac runner, installs the pinned official xtool release, then runs:

```sh
cd ipad
xtool dev build --ipa
```

The workflow uses a hosted Mac to build; it does not claim that this Windows PC has a fully configured WSL/Swift/Apple SDK toolchain. The resulting workflow artifact is an **unsigned development IPA**, not an App Store or TestFlight download. It must be signed to your own account before installation.

For local Windows builds, follow the upstream WSL, Swift and Apple SDK instructions. Obtain Xcode through your own Apple account and accept its license yourself. Apple credentials and SDKs are not uploaded to this repository or CI.

## Install the editor preview with a free Apple ID

Once xtool and iPad USB pairing are configured in WSL, use xtool's interactive authentication and installer:

```sh
xtool auth login
xtool devices
xtool install /path/to/OpenLabeliPad.ipa
```

Enter credentials only into the local interactive tool, never into chat or GitHub. xtool documents its use of private Apple APIs for password login and an Anisette service for device metadata. Follow its current instructions, including iPad trust/Developer Mode steps and free-account expiration/renewal limits. Signing the editor preview will not grant direct printer USB access.

The iPad source follows the repository's AGPL-3.0-only license. It uses Apple's built-in PDFKit, not PyMuPDF.
