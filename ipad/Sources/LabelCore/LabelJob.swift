import Foundation

public enum LabelError: Error, LocalizedError {
    case invalidSettings
    public var errorDescription: String? { "Check the image dimensions, label gap and copies." }
}

public enum LabelJob {
    public static let width = 813
    public static let height = 1219

    public static func encode(gray: [UInt8], width: Int = width, height: Int = height,
                              gap: Double = 3, copies: Int = 1, invert: Bool = false) throws -> Data {
        guard width > 0, width <= 832, height > 0, height <= 2400,
              gray.count == width * height, gap.isFinite, (0...10).contains(gap),
              (1...20).contains(copies) else { throw LabelError.invalidSettings }
        let stride = (width + 7) / 8
        var packed = [UInt8](repeating: 255, count: stride * height)
        for y in 0..<height {
            for x in 0..<width {
                let dark = (gray[y * width + x] < 128) != invert
                if dark { packed[y * stride + x / 8] &= ~(UInt8(128) >> (x % 8)) }
            }
        }
        let gapText = String(format: "%.1f", locale: Locale(identifier: "en_US_POSIX"), gap)
        let header = "SIZE 101.6 mm,152.4 mm\r\nGAP \(gapText) mm,0 mm\r\nREFERENCE 0,0\r\nDIRECTION 0\r\nCLS\r\nBITMAP 0,0,\(stride),\(height),1,"
        return Data(header.utf8) + Data(packed) + Data("\r\nPRINT 1,\(copies)\r\n".utf8)
    }
}
