//
//  QRScannerViewController.swift
//  EventyayOrganizer
//
//  Full-screen QR/barcode scanner using AVFoundation.
//  QR format expected: {order_identifier}-{attendee_id}
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import AVFoundation
import UIKit

protocol QRScannerDelegate: AnyObject {
    func scanner(_ scanner: QRScannerViewController, didScanAttendee attendee: AttendeeData)
    func scanner(_ scanner: QRScannerViewController, didFailWithMessage message: String)
}

class QRScannerViewController: UIViewController {

    // MARK: - Properties

    weak var delegate: QRScannerDelegate?
    var attendees: [AttendeeData] = []
    var eventName: String?

    private var captureSession = AVCaptureSession()
    private var previewLayer: AVCaptureVideoPreviewLayer?
    private var isPaused = false

    // MARK: - UI

    private let frameView = UIView()
    private let resultBanner = UIView()
    private let resultLabel = UILabel()
    private let torchButton = UIButton(type: .system)
    private let hintLabel = UILabel()

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        title = eventName.map { "Scan — \($0)" } ?? "Scan QR Code"
        navigationItem.leftBarButtonItem = UIBarButtonItem(
            barButtonSystemItem: .cancel,
            target: self,
            action: #selector(dismissScanner)
        )
        setupCamera()
        setupOverlay()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        if !captureSession.isRunning { captureSession.startRunning() }
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        if captureSession.isRunning { captureSession.stopRunning() }
    }

    // MARK: - Camera Setup

    private func setupCamera() {
        guard let device = AVCaptureDevice.default(for: .video) else {
            showResult("Camera not available", success: false)
            return
        }
        guard let input = try? AVCaptureDeviceInput(device: device) else {
            showResult("Cannot access camera", success: false)
            return
        }
        captureSession.addInput(input)

        let output = AVCaptureMetadataOutput()
        captureSession.addOutput(output)
        output.setMetadataObjectsDelegate(self, queue: .main)
        output.metadataObjectTypes = [.qr, .code128, .code39, .ean13, .ean8, .pdf417]

        let layer = AVCaptureVideoPreviewLayer(session: captureSession)
        layer.frame = view.layer.bounds
        layer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(layer)
        previewLayer = layer

        captureSession.startRunning()
    }

    // MARK: - Overlay UI

    private func setupOverlay() {
        // Dimmed area outside scan frame
        let dimView = UIView(frame: view.bounds)
        dimView.backgroundColor = UIColor.black.withAlphaComponent(0.5)
        dimView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(dimView)
        NSLayoutConstraint.activate([
            dimView.topAnchor.constraint(equalTo: view.topAnchor),
            dimView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            dimView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            dimView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        // Scan frame
        frameView.layer.borderColor = UIColor.white.cgColor
        frameView.layer.borderWidth = 2
        frameView.layer.cornerRadius = 8
        frameView.backgroundColor = .clear
        frameView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(frameView)
        let side: CGFloat = min(view.bounds.width, view.bounds.height) * 0.65
        NSLayoutConstraint.activate([
            frameView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            frameView.centerYAnchor.constraint(equalTo: view.centerYAnchor, constant: -40),
            frameView.widthAnchor.constraint(equalToConstant: side),
            frameView.heightAnchor.constraint(equalToConstant: side)
        ])

        // Hint label
        hintLabel.text = "Align QR code within the frame"
        hintLabel.textColor = .white
        hintLabel.textAlignment = .center
        hintLabel.font = UIFont.systemFont(ofSize: 14)
        hintLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(hintLabel)
        NSLayoutConstraint.activate([
            hintLabel.topAnchor.constraint(equalTo: frameView.bottomAnchor, constant: 20),
            hintLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor)
        ])

        // Torch button
        torchButton.setImage(UIImage(systemName: "flashlight.off.fill"), for: .normal)
        torchButton.tintColor = .white
        torchButton.translatesAutoresizingMaskIntoConstraints = false
        torchButton.addTarget(self, action: #selector(toggleTorch), for: .touchUpInside)
        view.addSubview(torchButton)
        NSLayoutConstraint.activate([
            torchButton.topAnchor.constraint(equalTo: hintLabel.bottomAnchor, constant: 20),
            torchButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            torchButton.widthAnchor.constraint(equalToConstant: 44),
            torchButton.heightAnchor.constraint(equalToConstant: 44)
        ])

        // Result banner (hidden initially)
        resultBanner.backgroundColor = UIColor.systemGreen
        resultBanner.translatesAutoresizingMaskIntoConstraints = false
        resultBanner.alpha = 0
        view.addSubview(resultBanner)
        NSLayoutConstraint.activate([
            resultBanner.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            resultBanner.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            resultBanner.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor),
            resultBanner.heightAnchor.constraint(equalToConstant: 60)
        ])

        resultLabel.textColor = .white
        resultLabel.textAlignment = .center
        resultLabel.font = UIFont.systemFont(ofSize: 15, weight: .semibold)
        resultLabel.translatesAutoresizingMaskIntoConstraints = false
        resultBanner.addSubview(resultLabel)
        NSLayoutConstraint.activate([
            resultLabel.centerYAnchor.constraint(equalTo: resultBanner.centerYAnchor),
            resultLabel.leadingAnchor.constraint(equalTo: resultBanner.leadingAnchor, constant: 16),
            resultLabel.trailingAnchor.constraint(equalTo: resultBanner.trailingAnchor, constant: -16)
        ])
    }

    // MARK: - Barcode Processing

    private func processBarcode(_ string: String) {
        guard !isPaused else { return }
        isPaused = true

        // Format: {order_identifier}-{attendee_id}
        let parts = string.split(separator: "-", maxSplits: 1).map(String.init)
        guard parts.count == 2, let attendeeId = parts.last else {
            showResult("Invalid QR code format", success: false)
            resumeAfterDelay()
            return
        }

        if let match = attendees.first(where: { $0.id == attendeeId }) {
            showResult("Found: \(match.attributes?.fullName ?? attendeeId)", success: true)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
                guard let self = self else { return }
                self.delegate?.scanner(self, didScanAttendee: match)
            }
        } else {
            showResult("Ticket not found in attendee list", success: false)
            resumeAfterDelay()
        }
    }

    private func resumeAfterDelay() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) { [weak self] in
            self?.isPaused = false
            self?.hideResult()
        }
    }

    // MARK: - UI Helpers

    private func showResult(_ message: String, success: Bool) {
        resultBanner.backgroundColor = success ? UIColor.systemGreen : UIColor.systemRed
        resultLabel.text = message
        frameView.layer.borderColor = (success ? UIColor.systemGreen : UIColor.systemRed).cgColor
        UIView.animate(withDuration: 0.2) { self.resultBanner.alpha = 1 }
    }

    private func hideResult() {
        UIView.animate(withDuration: 0.2) {
            self.resultBanner.alpha = 0
            self.frameView.layer.borderColor = UIColor.white.cgColor
        }
    }

    // MARK: - Actions

    @objc private func dismissScanner() {
        dismiss(animated: true)
    }

    @objc private func toggleTorch() {
        guard let device = AVCaptureDevice.default(for: .video), device.hasTorch else { return }
        try? device.lockForConfiguration()
        device.torchMode = device.torchMode == .on ? .off : .on
        device.unlockForConfiguration()
        let icon = device.torchMode == .on ? "flashlight.on.fill" : "flashlight.off.fill"
        torchButton.setImage(UIImage(systemName: icon), for: .normal)
    }

    // Called by delegate/parent to resume scanning after a confirmation is dismissed
    func resumeScanning() {
        isPaused = false
        hideResult()
        if !captureSession.isRunning { captureSession.startRunning() }
    }
}

// MARK: - AVCaptureMetadataOutputObjectsDelegate

extension QRScannerViewController: AVCaptureMetadataOutputObjectsDelegate {
    func metadataOutput(_ output: AVCaptureMetadataOutput,
                        didOutput metadataObjects: [AVMetadataObject],
                        from connection: AVCaptureConnection) {
        guard let object = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
              let string = object.stringValue else { return }
        processBarcode(string)
    }
}
