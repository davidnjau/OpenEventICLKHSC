//
//  AttendeesViewController.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import AVFoundation
import UIKit

class AttendeesViewController: UITableViewController {

    var eventId: String?
    var eventName: String?

    private var attendees: [AttendeeData] = []
    private var filtered: [AttendeeData] = []
    private let cellIdentifier = "AttendeeCell"
    private let searchController = UISearchController(searchResultsController: nil)

    private var isSearching: Bool {
        return searchController.isActive && !(searchController.searchBar.text?.isEmpty ?? true)
    }

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        title = eventName ?? "Attendees"
        navigationItem.rightBarButtonItem = UIBarButtonItem(
            image: UIImage(systemName: "qrcode.viewfinder"),
            style: .plain,
            target: self,
            action: #selector(scanQRTapped)
        )
        setupSearchController()
        tableView.register(AttendeeCell.self, forCellReuseIdentifier: cellIdentifier)
        tableView.rowHeight = 72
        loadAttendees()
    }

    // MARK: - Setup

    private func setupSearchController() {
        searchController.searchResultsUpdater = self
        searchController.obscuresBackgroundDuringPresentation = false
        searchController.searchBar.placeholder = "Search by name, email, company"
        navigationItem.searchController = searchController
        definesPresentationContext = true
    }

    // MARK: - Data

    private func loadAttendees() {
        guard let eventId = eventId else { return }
        AttendeeService.fetchAttendees(eventId: eventId) { [weak self] attendees in
            DispatchQueue.main.async {
                self?.attendees = attendees
                self?.tableView.reloadData()
            }
        }
    }

    // MARK: - UITableViewDataSource

    override func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        let source = isSearching ? filtered : attendees
        return source.isEmpty ? 1 : source.count
    }

    override func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let source = isSearching ? filtered : attendees
        if source.isEmpty {
            let cell = UITableViewCell()
            cell.textLabel?.text = attendees.isEmpty ? "No attendees found" : "No results"
            cell.textLabel?.textColor = .gray
            cell.selectionStyle = .none
            return cell
        }
        guard let cell = tableView.dequeueReusableCell(withIdentifier: cellIdentifier,
                                                       for: indexPath) as? AttendeeCell else {
            return UITableViewCell()
        }
        cell.configure(with: source[indexPath.row])
        return cell
    }

    // MARK: - UITableViewDelegate

    override func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        let source = isSearching ? filtered : attendees
        guard !source.isEmpty else { return }
        let detailVC = AttendeeDetailViewController()
        detailVC.attendee = source[indexPath.row]
        detailVC.onCheckInToggled = { [weak self] attendeeId, newState in
            self?.updateAttendeeLocally(id: attendeeId, isCheckedIn: newState)
        }
        navigationController?.pushViewController(detailVC, animated: true)
    }

    // MARK: - QR Scan

    @objc private func scanQRTapped() {
        AVFoundation.AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
            DispatchQueue.main.async {
                guard granted else {
                    let alert = UIAlertController(
                        title: "Camera Access Required",
                        message: "Enable camera access in Settings to scan QR codes.",
                        preferredStyle: .alert
                    )
                    alert.addAction(UIAlertAction(title: "OK", style: .default))
                    self?.present(alert, animated: true)
                    return
                }
                let scannerVC = QRScannerViewController()
                scannerVC.attendees = self?.attendees ?? []
                scannerVC.eventName = self?.eventName
                scannerVC.delegate = self
                let nav = UINavigationController(rootViewController: scannerVC)
                nav.modalPresentationStyle = .fullScreen
                self?.present(nav, animated: true)
            }
        }
    }

    // MARK: - Local State Update

    func updateAttendeeLocally(id: String, isCheckedIn: Bool) {
        if let idx = attendees.firstIndex(where: { $0.id == id }) {
            attendees[idx].attributes?.isCheckedIn = isCheckedIn
        }
        if let idx = filtered.firstIndex(where: { $0.id == id }) {
            filtered[idx].attributes?.isCheckedIn = isCheckedIn
        }
        tableView.reloadData()
    }
}

// MARK: - QRScannerDelegate

extension AttendeesViewController: QRScannerDelegate {
    func scanner(_ scanner: QRScannerViewController, didScanAttendee attendee: AttendeeData) {
        let confirmVC = CheckInConfirmViewController()
        confirmVC.attendee = attendee
        confirmVC.delegate = self
        confirmVC.modalPresentationStyle = .overFullScreen
        confirmVC.modalTransitionStyle = .crossDissolve
        scanner.present(confirmVC, animated: true)
    }

    func scanner(_ scanner: QRScannerViewController, didFailWithMessage message: String) {
        // banner already shown in scanner — nothing extra needed
    }
}

// MARK: - CheckInConfirmDelegate

extension AttendeesViewController: CheckInConfirmDelegate {
    func confirmDidDismiss(_ controller: CheckInConfirmViewController) {
        if let attendee = controller.attendee,
           let id = attendee.id,
           let newState = attendee.attributes?.isCheckedIn {
            updateAttendeeLocally(id: id, isCheckedIn: newState)
        }
        // Resume scanner
        if let nav = presentedViewController as? UINavigationController,
           let scanner = nav.topViewController as? QRScannerViewController {
            scanner.resumeScanning()
        }
    }
}

// MARK: - UISearchResultsUpdating

extension AttendeesViewController: UISearchResultsUpdating {
    func updateSearchResults(for searchController: UISearchController) {
        guard let query = searchController.searchBar.text?.lowercased(), !query.isEmpty else {
            filtered = []
            tableView.reloadData()
            return
        }
        filtered = attendees.filter { attendee in
            let attrs = attendee.attributes
            let name = attrs?.fullName.lowercased() ?? ""
            let email = attrs?.email?.lowercased() ?? ""
            let company = attrs?.company?.lowercased() ?? ""
            return name.contains(query) || email.contains(query) || company.contains(query)
        }
        tableView.reloadData()
    }
}

// MARK: - AttendeeCell

class AttendeeCell: UITableViewCell {

    private let nameLabel = UILabel()
    private let subtitleLabel = UILabel()
    private let badgeView = UIView()
    private let badgeLabel = UILabel()

    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupViews()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func setupViews() {
        nameLabel.font = UIFont.systemFont(ofSize: 16, weight: .medium)
        nameLabel.translatesAutoresizingMaskIntoConstraints = false

        subtitleLabel.font = UIFont.systemFont(ofSize: 13)
        subtitleLabel.textColor = .gray
        subtitleLabel.translatesAutoresizingMaskIntoConstraints = false

        badgeView.layer.cornerRadius = 10
        badgeView.translatesAutoresizingMaskIntoConstraints = false
        badgeView.widthAnchor.constraint(equalToConstant: 80).isActive = true
        badgeView.heightAnchor.constraint(equalToConstant: 20).isActive = true

        badgeLabel.font = UIFont.systemFont(ofSize: 11, weight: .semibold)
        badgeLabel.textColor = .white
        badgeLabel.textAlignment = .center
        badgeLabel.translatesAutoresizingMaskIntoConstraints = false
        badgeView.addSubview(badgeLabel)
        NSLayoutConstraint.activate([
            badgeLabel.centerXAnchor.constraint(equalTo: badgeView.centerXAnchor),
            badgeLabel.centerYAnchor.constraint(equalTo: badgeView.centerYAnchor)
        ])

        contentView.addSubview(nameLabel)
        contentView.addSubview(subtitleLabel)
        contentView.addSubview(badgeView)

        NSLayoutConstraint.activate([
            nameLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 12),
            nameLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            nameLabel.trailingAnchor.constraint(equalTo: badgeView.leadingAnchor, constant: -8),

            subtitleLabel.topAnchor.constraint(equalTo: nameLabel.bottomAnchor, constant: 3),
            subtitleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            subtitleLabel.trailingAnchor.constraint(equalTo: badgeView.leadingAnchor, constant: -8),

            badgeView.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
            badgeView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16)
        ])

        accessoryType = .disclosureIndicator
    }

    func configure(with attendee: AttendeeData) {
        let attrs = attendee.attributes
        nameLabel.text = attrs?.fullName
        let parts = [attrs?.company, attrs?.email].compactMap { $0 }.filter { !$0.isEmpty }
        subtitleLabel.text = parts.joined(separator: " · ")

        let checkedIn = attrs?.isCheckedIn ?? false
        badgeView.backgroundColor = checkedIn ? UIColor.systemGreen : UIColor.systemOrange
        badgeLabel.text = checkedIn ? "Checked In" : "Not In"
    }
}
