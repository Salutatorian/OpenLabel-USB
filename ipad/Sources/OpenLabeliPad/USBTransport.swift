#if canImport(UIKit)
import Foundation
import DriverBridge

struct USBPrintResult: Sendable {
    let status: Int32
    let sent: UInt64
}

actor USBTransport {
    static let shared = USBTransport()

    func send(_ data: Data) -> USBPrintResult {
        var sent: UInt64 = 0
        let status = data.withUnsafeBytes { bytes in
            OLPrintLabel(bytes.bindMemory(to: UInt8.self).baseAddress, data.count, &sent)
        }
        return USBPrintResult(status: status, sent: sent)
    }
}
#endif
