// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "OpenLabeliPad",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [.library(name: "OpenLabeliPad", targets: ["OpenLabeliPad"])],
    targets: [
        .target(name: "LabelCore"),
        .target(name: "DriverBridge", linkerSettings: [.linkedFramework("IOKit")]),
        .target(name: "OpenLabeliPad", dependencies: ["LabelCore", "DriverBridge"]),
        .testTarget(name: "LabelCoreTests", dependencies: ["LabelCore"])
    ]
)
