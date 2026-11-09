import XCTest
@testable import LabelCore

final class LabelCoreTests: XCTestCase {
    func testStockIsFourBySix() {
        XCTAssertEqual(LabelJob.width, 813)
        XCTAssertEqual(LabelJob.height, 1219)
    }
    func testPixelsPaddingAndFraming() throws {
        let image: [UInt8] = [0,255,255,255,255,255,255,255,0]
        let data = try LabelJob.encode(gray: image, width: 9, height: 1)
        let expected = Data("BITMAP 0,0,2,1,1,".utf8) + Data([0x7f,0x7f]) + Data("\r\nPRINT 1,1\r\n".utf8)
        XCTAssertTrue(data.suffix(expected.count).elementsEqual(expected))
        XCTAssertTrue(data.starts(with: Data("SIZE 101.6 mm,152.4 mm\r\n".utf8)))
    }
    func testRejectsInvalidSettings() {
        XCTAssertThrowsError(try LabelJob.encode(gray: [0], width: 1, height: 1, copies: 0))
        XCTAssertThrowsError(try LabelJob.encode(gray: [0], width: 2, height: 1))
        XCTAssertThrowsError(try LabelJob.encode(gray: [0], width: 1, height: 1, gap: .nan))
    }
    func testInvertedPolarity() throws {
        let data = try LabelJob.encode(gray: [0,0,0,0,0,0,0,0], width: 8, height: 1, invert: true)
        let expected = Data("BITMAP 0,0,1,1,1,".utf8) + Data([255]) + Data("\r\nPRINT 1,1\r\n".utf8)
        XCTAssertTrue(data.suffix(expected.count).elementsEqual(expected))
    }
}
