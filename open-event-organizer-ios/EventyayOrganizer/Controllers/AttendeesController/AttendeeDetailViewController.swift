//
//  AttendeeDetailViewController.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import UIKit

class AttendeeDetailViewController: UIViewController {

    var attendee: AttendeeData?
    /// Called after a successful check-in toggle so the list can refresh.
    var onCheckInToggled: ((_ attendeeId: String, _ newState: Bool) -> Void)?

    private let scrollView = UIScrollView()
    private let stackView = UIStackView()
    private var checkInButton: UIButton?

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .white
        title = attendee?.attributes?.fullName ?? "Attendee"
        setupScrollView()
        setupRows()
    }

    // MARK: - Layout

    private func setupScrollView() {
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)
        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        stackView.axis = .vertical
        stackView.spacing = 0
        stackView.translatesAutoresizingMaskIntoConstraints = false
        scrollView.addSubview(stackView)
        NSLayoutConstraint.activate([
            stackView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            stackView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            stackView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            stackView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            stackView.widthAnchor.constraint(equalTo: scrollView.widthAnchor)
        ])
    }

    private func setupRows() {
        guard let attrs = attendee?.attributes else { return }

        addCheckinBanner(isCheckedIn: attrs.isCheckedIn ?? false)
        addSectionHeader("Personal Info")
        addRow(label: "Full Name", value: attrs.fullName)
        addRow(label: "Email", value: attrs.email)
        addRow(label: "Phone", value: attrs.phone)
        addRow(label: "Gender", value: attrs.gender)

        addSectionHeader("Organisation")
        addRow(label: "Company", value: attrs.company)
        addRow(label: "Job Title", value: attrs.jobTitle)

        addSectionHeader("Location")
        addRow(label: "Address", value: attrs.address)
        addRow(label: "City", value: attrs.city)
        addRow(label: "State", value: attrs.state)
        addRow(label: "Country", value: attrs.country)

        addSectionHeader("Check-In")
        addRow(label: "Status", value: (attrs.isCheckedIn ?? false) ? "Checked In" : "Not Checked In")
        addRow(label: "Check-In Time", value: attrs.checkinTimes ?? "—")
        addRow(label: "Device", value: attrs.deviceNameCheckin)
        addRow(label: "Identifier", value: attrs.identifier)
        addCheckInButton()
    }

    private func addCheckInButton() {
        let isCheckedIn = attendee?.attributes?.isCheckedIn ?? false
        let container = UIView()
        container.translatesAutoresizingMaskIntoConstraints = false

        let button = UIButton(type: .system)
        button.backgroundColor = isCheckedIn ? UIColor.systemOrange : UIColor.systemGreen
        button.setTitleColor(.white, for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 17, weight: .semibold)
        button.layer.cornerRadius = 8
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(toggleCheckIn), for: .touchUpInside)
        checkInButton = button
        refreshCheckInButton()

        container.addSubview(button)
        NSLayoutConstraint.activate([
            button.topAnchor.constraint(equalTo: container.topAnchor, constant: 20),
            button.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            button.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -16),
            button.heightAnchor.constraint(equalToConstant: 50),
            button.bottomAnchor.constraint(equalTo: container.bottomAnchor, constant: -20)
        ])
        stackView.addArrangedSubview(container)
    }

    private func refreshCheckInButton() {
        let isCheckedIn = attendee?.attributes?.isCheckedIn ?? false
        checkInButton?.setTitle(isCheckedIn ? "Check Out" : "Check In", for: .normal)
        checkInButton?.backgroundColor = isCheckedIn ? UIColor.systemOrange : UIColor.systemGreen
    }

    @objc private func toggleCheckIn() {
        guard let attendeeId = attendee?.id else { return }
        let newState = !(attendee?.attributes?.isCheckedIn ?? false)
        checkInButton?.isEnabled = false

        CheckInService.toggleCheckIn(attendeeId: attendeeId, isCheckedIn: newState) { [weak self] success, error in
            guard let self = self else { return }
            DispatchQueue.main.async {
                self.checkInButton?.isEnabled = true
                if success {
                    self.attendee?.attributes?.isCheckedIn = newState
                    self.refreshCheckInButton()
                    self.onCheckInToggled?(attendeeId, newState)
                    // Refresh the check-in banner and rows
                    self.stackView.arrangedSubviews.forEach { $0.removeFromSuperview() }
                    self.setupRows()
                } else {
                    let alert = UIAlertController(title: "Error",
                                                  message: error ?? "Unknown error",
                                                  preferredStyle: .alert)
                    alert.addAction(UIAlertAction(title: "OK", style: .default))
                    self.present(alert, animated: true)
                }
            }
        }
    }

    // MARK: - Row builders

    private func addCheckinBanner(isCheckedIn: Bool) {
        let banner = UIView()
        banner.backgroundColor = isCheckedIn ? UIColor.systemGreen : UIColor.systemOrange
        banner.translatesAutoresizingMaskIntoConstraints = false

        let label = UILabel()
        label.text = isCheckedIn ? "✓  Checked In" : "✗  Not Checked In"
        label.textColor = .white
        label.font = UIFont.systemFont(ofSize: 17, weight: .semibold)
        label.textAlignment = .center
        label.translatesAutoresizingMaskIntoConstraints = false

        banner.addSubview(label)
        NSLayoutConstraint.activate([
            label.topAnchor.constraint(equalTo: banner.topAnchor, constant: 14),
            label.bottomAnchor.constraint(equalTo: banner.bottomAnchor, constant: -14),
            label.leadingAnchor.constraint(equalTo: banner.leadingAnchor, constant: 16),
            label.trailingAnchor.constraint(equalTo: banner.trailingAnchor, constant: -16)
        ])
        stackView.addArrangedSubview(banner)
    }

    private func addSectionHeader(_ title: String) {
        let header = UIView()
        header.backgroundColor = UIColor(white: 0.95, alpha: 1)
        header.translatesAutoresizingMaskIntoConstraints = false

        let label = UILabel()
        label.text = title.uppercased()
        label.font = UIFont.systemFont(ofSize: 12, weight: .semibold)
        label.textColor = .gray
        label.translatesAutoresizingMaskIntoConstraints = false

        header.addSubview(label)
        NSLayoutConstraint.activate([
            label.topAnchor.constraint(equalTo: header.topAnchor, constant: 8),
            label.bottomAnchor.constraint(equalTo: header.bottomAnchor, constant: -8),
            label.leadingAnchor.constraint(equalTo: header.leadingAnchor, constant: 16),
            label.trailingAnchor.constraint(equalTo: header.trailingAnchor, constant: -16)
        ])
        stackView.addArrangedSubview(header)
    }

    private func addRow(label: String, value: String?) {
        let container = UIView()
        container.translatesAutoresizingMaskIntoConstraints = false

        let separator = UIView()
        separator.backgroundColor = UIColor(white: 0.9, alpha: 1)
        separator.translatesAutoresizingMaskIntoConstraints = false

        let labelView = UILabel()
        labelView.text = label
        labelView.font = UIFont.systemFont(ofSize: 12, weight: .medium)
        labelView.textColor = .gray
        labelView.translatesAutoresizingMaskIntoConstraints = false

        let valueView = UILabel()
        valueView.text = value?.isEmpty == false ? value : "—"
        valueView.font = UIFont.systemFont(ofSize: 16)
        valueView.textColor = .black
        valueView.translatesAutoresizingMaskIntoConstraints = false

        container.addSubview(labelView)
        container.addSubview(valueView)
        container.addSubview(separator)

        NSLayoutConstraint.activate([
            labelView.topAnchor.constraint(equalTo: container.topAnchor, constant: 10),
            labelView.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            labelView.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -16),

            valueView.topAnchor.constraint(equalTo: labelView.bottomAnchor, constant: 2),
            valueView.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            valueView.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -16),
            valueView.bottomAnchor.constraint(equalTo: separator.topAnchor, constant: -10),

            separator.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            separator.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            separator.bottomAnchor.constraint(equalTo: container.bottomAnchor),
            separator.heightAnchor.constraint(equalToConstant: 0.5)
        ])
        stackView.addArrangedSubview(container)
    }
}
