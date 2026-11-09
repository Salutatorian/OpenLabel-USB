# MHT-L1081 USB driver development

This is original USBDriverKit transport code for the standalone **iPad + powered printer** setup. It does not require a PC or network at print time. It is a development implementation, not a physically validated printer release.

## Components

- `OpenLabelUSBDriver`: opens the matching printer-class interface and discovers its bulk OUT endpoint from configuration descriptors. It does not assume endpoint 1.
- `OpenLabelUSBUserClient`: receives one complete job through bounded Begin/Append/Commit calls. Appends do not send bytes to the printer. Jobs are capped at 128 KiB and inline chunks at 2048 bytes. Commit discards the staged job even after an error to avoid automatic duplicate retries.
- `DriverBridge`: native app calls to the IOService and user-client methods. The iPad's Print over USB action uses this bridge and reports the actual transfer result, not a simulated success.
- Pure C++ descriptor tests plus the existing Swift encoder tests run in CI. Neither sends printer commands.

The VID/PID `0FE6:811E` is shared by some other devices. This development personality matches that pair and printer-class interfaces. Use it only with the investigated MHT-L1081. Broader device identification and physical matching must be verified before public distribution.

## Build

On an Apple build host with Xcode and XcodeGen:

```sh
clang++ -std=c++17 -Wall -Wextra -Werror test_descriptors.cpp -o /tmp/usb-tests
/tmp/usb-tests
xcodegen generate
xcodebuild -project OpenLabelUSBDriver.xcodeproj -scheme OpenLabelUSBDriver \
  -configuration Debug -sdk driverkit -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO ARCHS=arm64
```

The GitHub iPad development workflow builds this extension and the app with xtool. `bundle_driver.py` verifies the DEXT's ARM64/DriverKit Mach-O identity and embeds it under the iPad app's `Library/SystemExtensions` directory. The resulting `OpenLabeliPad-USB-UNSIGNED.ipa` is deliberately labeled **not install-ready**.

## Signing and physical testing remain required

A compiling DEXT is not permission to run it. The app requires `com.apple.developer.driverkit.communicates-with-drivers`; the DEXT requires DriverKit and the USB transport entitlement covering the device. The supplied entitlement files are templates, not approved provisioning profiles.

Before a device test, a developer team must obtain appropriate Apple app IDs/profiles/certificates and sign both the extension and host app with matching identifiers/entitlements. The extension uses the same-team default user-client restriction and does not request access by arbitrary apps. The iPad user must enable the installed driver in Settings. Ordinary free-account signing of the earlier editor preview does not accomplish this.

End users do not need paid membership merely to use a properly distributed, signed app. This requirement concerns the development/distribution signing team. Buying membership alone does not establish that all requested transport permissions will be approved.

Physical testing must confirm interface matching, raster orientation, gap behavior, USB timeout/partial-write handling, and label output. The desktop printer test does not establish that this DEXT works on iPad.

No firmware flashing, OS permission bypass, network bridge, or vendor binary is included.

## API references

- [Apple DriverKit sample](https://developer.apple.com/documentation/driverkit/communicating-between-a-driverkit-extension-and-a-client-app)
- [USBDriverKit](https://developer.apple.com/documentation/usbdriverkit)
- [iPad driver deployment](https://developer.apple.com/documentation/driverkit/creating-drivers-for-ipados)
- [DriverKit provisioning](https://developer.apple.com/help/account/provisioning-profiles/create-a-driverkit-development-provisioning-profile)

The Apple sample informed the lifecycle and IIG integration; its permissive license is included as `Apple-sample-LICENSE.txt`. The application and new driver sources follow this repository's AGPL-3.0-only license.
