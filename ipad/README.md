# OpenLabel for iPad — xtool development build

**This is USB-driver development work, not a device-tested printing release.** It builds with [xtool 1.24.0](https://github.com/xtool-org/xtool/releases/tag/1.24.0). The desktop releases remain separate.

## What is implemented

- Native SwiftUI iPad interface, portrait and landscape.
- Fixed 4 x 6 stock, live text preview, image and first-page PDF import from Files.
- Independent Swift TSPL encoder matching the tested Windows byte format.
- Export/share PNG and raw `.prn` files.

## What is not implemented or validated

A USBDriverKit extension, native IOKit app bridge, and Print over USB action are implemented. The extension and app compile on Apple tooling, and the workflow embeds the DEXT in an unsigned development IPA. **No properly provisioned driver has been installed or physically tested on an iPad.** The earlier editor preview was successfully sideloaded by the owner, but that does not validate the new driver. See [driver development notes](Driver/README.md).

## Why xtool helps, and where it stops

xtool supports app building/signing/installation on Windows through WSL. Its current packager models applications and ordinary `.appex` extensions, not DriverKit `.dext` products. A regular/free Apple ID can provision ordinary apps subject to Apple's limits; it does not supply the DriverKit provisioning needed for this printer connection. A paid account alone does not mean all required USB entitlements have been approved. You do not need a paid membership merely to use a properly distributed app; the requirement applies to the team that builds/signs the driver. A future driver-equipped release could be distributed to regular users.

The remaining direct-USB work requires matching DriverKit-enabled app/driver provisioning, valid device signing, user driver enablement, and physical testing on the M-series iPad. The new implementation discovers its bulk OUT endpoint, stages bounded complete jobs, and uses a native user-client connection. No vendor firmware or driver binary is reused.

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

The workflow uses a hosted Mac to build; it does not claim that this Windows PC has a fully configured WSL/Swift/Apple SDK toolchain. The resulting workflow artifact is **OpenLabel-iPad-USB-requires-DriverKit-signing**, not an App Store or TestFlight download. It contains an unsigned host app and embedded DEXT plus entitlement templates. Ordinary free-account sideloading is insufficient for this driver build; real matching DriverKit provisioning is required.

For local Windows builds, follow the upstream WSL, Swift and Apple SDK instructions. Obtain Xcode through your own Apple account and accept its license yourself. Apple credentials and SDKs are not uploaded to this repository or CI.

## Earlier editor preview only: install with a free Apple ID

Once xtool and iPad USB pairing are configured in WSL, use xtool's interactive authentication and installer:

```sh
xtool auth login
xtool devices
xtool install /path/to/OpenLabeliPad.ipa
```

Enter credentials only into the local interactive tool, never into chat or GitHub. xtool documents its use of private Apple APIs for password login and an Anisette service for device metadata. Follow its current instructions, including iPad trust/Developer Mode steps and free-account expiration/renewal limits. Signing the editor preview will not grant direct printer USB access.

The iPad source follows the repository's AGPL-3.0-only license. It uses Apple's built-in PDFKit, not PyMuPDF.

A Windows install helper is provided as `install-preview.ps1`. It requires an already configured regular WSL distribution and iPad pairing. It downloads pinned official xtool 1.24.0, keeps authentication interactive, and installs only the editor preview. The helper has been syntax-checked but has not been run against a physical iPad.
