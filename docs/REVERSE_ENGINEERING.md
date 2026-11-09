# MHT-L1081 interoperability investigation

The owner wanted an app they could understand and control without depending on an unknown installer. Uncertainty about an installer is not evidence of malware. The investigation was limited to the supplied MHT-L1081 package and matching installed Windows driver.

## Method and evidence

1. Used the official **rea-agents 6.7.0** CLI's `inspect-artifact` operation on the supplied Windows utility DLL, extracted Linux raster filter, and installed Windows rendering DLL. REA returned inventory and SHA-256 identities; it did not decompile the driver for us.
2. No supported native decompiler was configured in REA. Supplementary ASCII/UTF-16 extraction, PE/ELF parsing and Capstone disassembly established command references.
3. The supplied Linux `MHT-L1081.ppd` explicitly declares `RTLanguage: TSPL2` and 203 dpi. Both the Windows renderer and Linux filter contain `SIZE`, `GAP`, `BITMAP`, and `PRINT` templates.
4. In the inspected Windows rendering DLL, function RVA `0x8b5c` formats `BITMAP 0,0,%d,%d,1,`, outputs the binary raster, then `PRINT 1,1`. Function RVA `0x8c70` formats dimensions and media settings. These are observations of one binary, not recovered original source.
5. The actual printer identified as MHT-L1081 with VID/PID `0FE6:811E`. Direct USB access worked through Microsoft's built-in `usbprint.sys` / `usbprint.inf`.
6. Wrote an independent raster encoder. The owner read back the expected test text, then uninstalled the MHT driver. A second direct USB test printed the expected text again.

This supports Windows interoperability on the tested unit. It does not establish universal TSPL2 support, every vendor feature, or Mac/iPad compatibility. Mac physical testing remains outstanding.

## Encoding

Fixed stock: 101.6 x 152.4 mm. Raster: 813 x 1219 dots at 8 dots/mm, MSB-first packed rows, white padding, observed bitmap mode 1. Gap is configurable. Jobs combine ASCII headers with CRLF and binary raster data.

The VID/PID is shared by other hardware, so discovery also checks the reported model. A matching VID/PID alone is not general printer compatibility.

## References

- [REA](https://github.com/morluto/rea)
- [Microsoft USB printer driver](https://learn.microsoft.com/en-us/windows-hardware/drivers/print/usb-printing)
- [Microsoft bus-reported device description](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-device-busreporteddevicedesc)
- [PyUSB](https://github.com/pyusb/pyusb) and [libusb](https://github.com/libusb/libusb)

Only original app source and sanitized findings are published. Local paths, printer serial numbers, raw vendor binaries, labels with personal data, and installer packages are excluded.
