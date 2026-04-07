//
//  EventDetailViewController.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import UIKit

class EventDetailViewController: UIViewController {

    var event: EventData?

    // MARK: - UI Elements

    private let scrollView = UIScrollView()
    private let stackView = UIStackView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .white
        title = event?.attributes?.name ?? "Event"
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
        guard let attrs = event?.attributes else { return }

        addRow(label: "Event ID", value: event?.id)
        addRow(label: "Name", value: attrs.name)
        addRow(label: "State", value: attrs.state?.capitalized)
        addRow(label: "Starts At", value: formatDate(attrs.startsAt))
        addRow(label: "Ends At", value: formatDate(attrs.endsAt))
        addRow(label: "Identifier", value: attrs.identifier)

        if let desc = attrs.description, !desc.isEmpty {
            addRow(label: "Description", value: desc, multiline: true)
        }

        addAttendeesButton()
    }

    private func addRow(label: String, value: String?, multiline: Bool = false) {
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
        valueView.text = value ?? "—"
        valueView.font = UIFont.systemFont(ofSize: 16)
        valueView.textColor = .black
        valueView.translatesAutoresizingMaskIntoConstraints = false
        if multiline {
            valueView.numberOfLines = 0
        }

        container.addSubview(labelView)
        container.addSubview(valueView)
        container.addSubview(separator)

        NSLayoutConstraint.activate([
            labelView.topAnchor.constraint(equalTo: container.topAnchor, constant: 12),
            labelView.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            labelView.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -16),

            valueView.topAnchor.constraint(equalTo: labelView.bottomAnchor, constant: 2),
            valueView.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            valueView.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -16),
            valueView.bottomAnchor.constraint(equalTo: separator.topAnchor, constant: -12),

            separator.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            separator.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            separator.bottomAnchor.constraint(equalTo: container.bottomAnchor),
            separator.heightAnchor.constraint(equalToConstant: 0.5)
        ])

        stackView.addArrangedSubview(container)
    }

    private func addAttendeesButton() {
        let container = UIView()
        container.translatesAutoresizingMaskIntoConstraints = false

        let button = UIButton(type: .system)
        button.setTitle("View Attendees", for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 17, weight: .semibold)
        button.backgroundColor = UIColor(red: 0.2, green: 0.5, blue: 1.0, alpha: 1)
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(attendeesTapped), for: .touchUpInside)

        container.addSubview(button)
        NSLayoutConstraint.activate([
            button.topAnchor.constraint(equalTo: container.topAnchor, constant: 24),
            button.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            button.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -16),
            button.heightAnchor.constraint(equalToConstant: 50),
            button.bottomAnchor.constraint(equalTo: container.bottomAnchor, constant: -24)
        ])

        stackView.addArrangedSubview(container)
    }

    // MARK: - Actions

    @objc private func attendeesTapped() {
        // Attendees screen — to be implemented
        let alert = UIAlertController(
            title: "Coming Soon",
            message: "Attendees list for this event will be available here.",
            preferredStyle: .alert
        )
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    // MARK: - Helpers

    private func formatDate(_ iso: String?) -> String? {
        guard let iso = iso else { return nil }
        let parser = ISO8601DateFormatter()
        parser.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = parser.date(from: iso) else { return iso }
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}
