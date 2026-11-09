#if canImport(UIKit)
import SwiftUI
import UIKit
import PDFKit
import UniformTypeIdentifiers
import LabelCore
import DriverBridge

@main
struct OpenLabelApp: App {
    var body: some Scene {
        WindowGroup { LabelEditor() }
    }
}

private enum EditorError: Error, LocalizedError {
    case unreadableFile, renderFailed, tooMuchText
    var errorDescription: String? {
        switch self {
        case .unreadableFile: "Could not open that image or PDF. Password-protected PDFs are not supported."
        case .renderFailed: "Could not render the label."
        case .tooMuchText: "The text is too tall for a 4 x 6 label. Reduce the text size."
        }
    }
}

private enum Raster {
    static let size = CGSize(width: LabelJob.width, height: LabelJob.height)

    static func draw(text: String, fontPoints: Double, image: UIImage?) throws -> UIImage {
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        format.opaque = true
        let bounds = CGRect(origin: .zero, size: size)
        let content = bounds.insetBy(dx: 16, dy: 16)
        let attributes: [NSAttributedString.Key: Any] = [
            .font: UIFont.systemFont(ofSize: fontPoints * 203 / 72),
            .foregroundColor: UIColor.black
        ]
        if image == nil {
            let measured = (text as NSString).boundingRect(with: CGSize(width: content.width, height: .greatestFiniteMagnitude),
                options: [.usesLineFragmentOrigin, .usesFontLeading], attributes: attributes, context: nil)
            guard measured.height <= content.height else { throw EditorError.tooMuchText }
        }
        return UIGraphicsImageRenderer(size: size, format: format).image { renderer in
            UIColor.white.setFill()
            renderer.fill(bounds)
            if let image {
                let scale = min(content.width / image.size.width, content.height / image.size.height)
                let fitted = CGSize(width: image.size.width * scale, height: image.size.height * scale)
                image.draw(in: CGRect(x: (size.width-fitted.width)/2, y: (size.height-fitted.height)/2,
                                      width: fitted.width, height: fitted.height))
            } else {
                (text as NSString).draw(with: content, options: [.usesLineFragmentOrigin, .usesFontLeading],
                                       attributes: attributes, context: nil)
            }
        }
    }

    static func gray(_ image: UIImage) throws -> [UInt8] {
        guard let cgImage = image.cgImage else { throw EditorError.renderFailed }
        var bytes = [UInt8](repeating: 255, count: LabelJob.width * LabelJob.height)
        let succeeded = bytes.withUnsafeMutableBytes { buffer -> Bool in
            guard let context = CGContext(data: buffer.baseAddress, width: LabelJob.width, height: LabelJob.height,
                bitsPerComponent: 8, bytesPerRow: LabelJob.width, space: CGColorSpaceCreateDeviceGray(), bitmapInfo: 0)
            else { return false }
            context.draw(cgImage, in: CGRect(origin: .zero, size: size))
            return true
        }
        guard succeeded else { throw EditorError.renderFailed }
        return bytes
    }

    static func importFile(_ url: URL) throws -> UIImage {
        if url.pathExtension.lowercased() == "pdf" {
            guard let pdf = PDFDocument(url: url), !pdf.isLocked, let page = pdf.page(at: 0) else {
                throw EditorError.unreadableFile
            }
            return page.thumbnail(of: size, for: .mediaBox)
        }
        guard let image = UIImage(contentsOfFile: url.path), image.size.width > 0, image.size.height > 0 else {
            throw EditorError.unreadableFile
        }
        return image
    }
}

private struct ExportFile: FileDocument {
    static var readableContentTypes: [UTType] { [.data, .png] }
    var data: Data
    init(data: Data = Data()) { self.data = data }
    init(configuration: ReadConfiguration) throws {
        data = configuration.file.regularFileContents ?? Data()
    }
    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper {
        FileWrapper(regularFileWithContents: data)
    }
}

private struct LabelEditor: View {
    @Environment(\.scenePhase) private var scenePhase
    @State private var usbStatus: Int32 = -1
    @State private var printing = false
    @State private var printResult: String?
    @State private var text = "MY FIRST LABEL\nMade with OpenLabel"
    @State private var fontSize = 24.0
    @State private var gap = 3.0
    @State private var copies = 1
    @State private var imported: UIImage?
    @State private var source = "Editable text"
    @State private var preview: UIImage?
    @State private var message: String?
    @State private var choosingFile = false
    @State private var exporting = false
    @State private var exportFile = ExportFile()
    @State private var exportName = "label.prn"
    @State private var exportType = UTType.data

    var body: some View {
        NavigationStack {
            GeometryReader { geometry in
                ScrollView {
                    if geometry.size.width > 800 {
                        HStack(alignment: .top, spacing: 24) {
                            controls.frame(width: 300)
                            previewPanel.frame(maxWidth: .infinity)
                        }.padding(24)
                    } else {
                        VStack(spacing: 20) { previewPanel; controls }.padding(16)
                    }
                }
                .background(Color(uiColor: .systemGroupedBackground))
            }
            .navigationTitle("OpenLabel")
            .safeAreaInset(edge: .bottom) {
                VStack(spacing: 8) {
                    if let message { Text(message).font(.callout).foregroundStyle(.red) }
                    HStack {
                        Button("Save PNG", systemImage: "photo") { prepareExport(png: true) }
                        Spacer()
                        Button("Export print file", systemImage: "square.and.arrow.up") { prepareExport(png: false) }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(preview == nil || printing)
                    Button(printing ? "Printing..." : "Print over USB", systemImage: "printer") { printUSB() }
                        .buttonStyle(.borderedProminent)
                        .disabled(preview == nil || usbStatus != 0 || printing)
                    if let printResult { Text(printResult).font(.callout) }
                }
                .padding().background(.regularMaterial)
            }
        }
        .onAppear { updatePreview(); checkUSB() }
        .onChange(of: scenePhase) { _, phase in if phase == .active { checkUSB() } }
        .onChange(of: text) { _, _ in
            imported = nil
            source = "Editable text"
            updatePreview()
        }
        .onChange(of: fontSize) { _, _ in updatePreview() }
        .fileImporter(isPresented: $choosingFile, allowedContentTypes: [.image, .pdf]) { result in
            do {
                let url = try result.get()
                let access = url.startAccessingSecurityScopedResource()
                defer { if access { url.stopAccessingSecurityScopedResource() } }
                imported = try Raster.importFile(url)
                source = url.lastPathComponent + (url.pathExtension.lowercased() == "pdf" ? " (page 1)" : "")
                updatePreview()
            } catch { message = error.localizedDescription }
        }
        .fileExporter(isPresented: $exporting, document: exportFile, contentType: exportType,
                      defaultFilename: exportName) { result in
            if case .failure(let error) = result { message = error.localizedDescription }
        }
    }

    private var controls: some View {
        VStack(alignment: .leading, spacing: 16) {
            GroupBox("Label stock") {
                VStack(alignment: .leading, spacing: 12) {
                    Text("4 × 6 inches").font(.headline)
                    Text("101.6 × 152.4 mm").foregroundStyle(.secondary)
                    Stepper("Copies: \(copies)", value: $copies, in: 1...20)
                    Stepper("Gap: \(gap, specifier: "%.1f") mm", value: $gap, in: 0...10, step: 0.5)
                }.frame(maxWidth: .infinity, alignment: .leading)
            }
            Text("Type text or import a file").font(.headline)
            TextEditor(text: $text)
                .frame(minHeight: 120)
                .padding(8).background(.background, in: RoundedRectangle(cornerRadius: 12))
                .accessibilityLabel("Label text")
            HStack {
                Text("Text size: \(Int(fontSize)) pt")
                Slider(value: $fontSize, in: 6...72, step: 1).accessibilityLabel("Text size")
            }
            Button("Import image or PDF", systemImage: "doc.badge.plus") { choosingFile = true }
                .buttonStyle(.bordered)
            Text(source).font(.caption).foregroundStyle(.secondary).lineLimit(3)
            GroupBox("USB printer") {
                VStack(alignment: .leading, spacing: 8) {
                    Text(usbStatus == 0 ? "USB driver connected" : "USB driver unavailable (0x" + String(UInt32(bitPattern: usbStatus), radix: 16) + ")")
                    Text("Connect the powered printer and enable the properly signed OpenLabel driver in Settings > General > Drivers. This development build still requires DriverKit provisioning.").font(.callout)
                    Button("Refresh USB printer") { checkUSB() }
                }.frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    private var previewPanel: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Preview").font(.headline)
            if let preview {
                Image(uiImage: preview).resizable().interpolation(.none)
                    .aspectRatio(2.0/3.0, contentMode: .fit)
                    .frame(maxHeight: 650)
                    .background(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 4))
                    .accessibilityLabel("Current 4 by 6 label preview")
            } else {
                ContentUnavailableView("Check label content", systemImage: "doc", description: Text(message ?? ""))
            }
        }
    }

    private func checkUSB() {
        guard !printing else { return }
        usbStatus = OLDriverStatus()
    }

    private func printUSB() {
        do {
            guard !printing, usbStatus == 0, let preview else { return }
            let data = try LabelJob.encode(gray: Raster.gray(preview), gap: gap, copies: copies)
            printing = true
            printResult = nil
            Task {
                let result = await USBTransport.shared.send(data)
                printing = false
                if result.status == 0 {
                    printResult = "Sent \(result.sent) bytes over USB. Check the physical label."
                } else {
                    printResult = "USB error 0x" + String(UInt32(bitPattern: result.status), radix: 16) + ". Check the printer before retrying; the job may have partly printed."
                }
                checkUSB()
            }
        } catch { message = error.localizedDescription }
    }

    private func updatePreview() {
        do {
            preview = try Raster.draw(text: text, fontPoints: fontSize, image: imported)
            message = nil
        } catch { preview = nil; message = error.localizedDescription }
    }

    private func prepareExport(png: Bool) {
        do {
            guard let preview else { throw EditorError.renderFailed }
            let data: Data
            if png {
                guard let encoded = preview.pngData() else { throw EditorError.renderFailed }
                data = encoded
            } else {
                data = try LabelJob.encode(gray: Raster.gray(preview), gap: gap, copies: copies)
            }
            exportFile = ExportFile(data: data)
            exportName = png ? "label.png" : "label.prn"
            exportType = png ? .png : .data
            exporting = true
        } catch { message = error.localizedDescription }
    }
}
#endif
