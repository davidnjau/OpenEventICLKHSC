//
//  CheckInConfirmViewController.swift
//  EventyayOrganizer
//
//  Bottom-sheet confirmation shown after a QR scan.
//  Mirrors the Android AttendeeCheckInFragment behaviour.
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import UIKit

protocol CheckInConfirmDelegate: AnyObject {
    func confirmDidDismiss(_ controller: CheckInConfirmViewController)
}

class CheckInConfirmViewController: UIViewController {

    // MARK: - Properties

    var attendee: AttendeeData?
    weak var delegate: CheckInConfirmDelegate?

    private var isCheckedIn: Bool = false
    private let containerView = UIView()

    // MARK: - UI

    private let handleBar = UIView()
    private let nameLabel = UILabel()
    private let emailLabel = UILabel()
    private let companyLabel = UILabel()
    private let identifierLabel = UILabel()
    private let statusBanner = UIView()
    private let statusLabel = UILabel()
    private let toggleButton = UIButton(type: .system)
    private let continueButton = UIButton(type: .system)
    private let activityIndicator = UIActivityIndicatorView(style: .medium)

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor.black.withAlphaComponent(0.4)
        isCheckedIn = attendee?.attributes?.isCheckedIn ?? false
        setupContainer()
        populate()

        let tap = UITapGestureRecognizer(target: self, action: #selector(backgroundTapped))
        view.addGestureRecognizer(tap)
        containerView.addGestureRecognizer(UITapGestureRecognizer()) // absorb taps inside container
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        animateIn()
    }

    // MARK: - Layout

    private func setupContainer() {
        containerView.backgroundColor = .white
        containerView.layer.cornerRadius = 16
        containerView.layer.maskedCorners = [.layerMinXMinYCorner, .layerMaxXMinYCorner]
        containerView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(containerView)
        NSLayoutConstraint.activate([
            containerView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            containerView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            containerView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        handleBar.backgroundColor = UIColor(white: 0.8, alpha: 1)
        handleBar.layer.cornerRadius = 2.5
        handleBar.translatesAutoresizingMaskIntoConstraints = false
        containerView.addSubview(handleBar)

        let stack = UIStackView()
        stack.axis = .vertical
        stack.spacing = 6
        stack.translatesAutoresizingMaskIntoConstraints = false
        containerView.addSubview(stack)

        for label in [nameLabel, emailLabel, companyLabel, identifierLabel] {
            stack.addArrangedSubview(label)
        }

        statusBanner.layer.cornerRadius = 8
        statusBanner.translatesAutoresizingMaskIntoConstraints = false
        statusBanner.heightAnchor.constraint(equalToConstant: 44).isActive = true
        statusBanner.addSubview(statusLabel)
        statusLabel.textColor = .white
        statusLabel.font = UIFont.systemFont(ofSize: 15, weight: .semibold)
        statusLabel.textAlignment = .center
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            statusLabel.centerXAnchor.constraint(equalTo: statusBanner.centerXAnchor),
            statusLabel.centerYAnchor.constraint(equalTo: statusBanner.centerYAnchor)
        ])

        toggleButton.titleLabel?.font = UIFont.systemFont(ofSize: 16, weight: .semibold)
        toggleButton.layer.cornerRadius = 8
        toggleButton.translatesAutoresizingMaskIntoConstraints = false
        toggleButton.heightAnchor.constraint(equalToConstant: 50).isActive = true
        toggleButton.addTarget(self, action: #selector(toggleTapped), for: .touchUpInside)

        continueButton.setTitle("Continue Scanning", for: .normal)
        continueButton.titleLabel?.font = UIFont.systemFont(ofSize: 16)
        continueButton.layer.cornerRadius = 8
        continueButton.layer.borderWidth = 1
        continueButton.layer.borderColor = UIColor.systemBlue.cgColor
        continueButton.translatesAutoresizingMaskIntoConstraints = false
        continueButton.heightAnchor.constraint(equalToConstant: 50).isActive = true
        continueButton.addTarget(self, action: #selector(continueTapped), for: .touchUpInside)

        activityIndicator.translatesAutoresizingMaskIntoConstraints = false
        activityIndicator.hidesWhenStopped = true

        NSLayoutConstraint.activate([
            handleBar.topAnchor.constraint(equalTo: containerView.topAnchor, constant: 12),
            handleBar.centerXAnchor.constraint(equalTo: containerView.centerXAnchor),
            handleBar.widthAnchor.constraint(equalToConstant: 40),
            handleBar.heightAnchor.constraint(equalToConstant: 5),

            stack.topAnchor.constraint(equalTo: handleBar.bottomAnchor, constant: 20),
            stack.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -20),

            statusBanner.topAnchor.constraint(equalTo: stack.bottomAnchor, constant: 16),
            statusBanner.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 20),
            statusBanner.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -20),

            toggleButton.topAnchor.constraint(equalTo: statusBanner.bottomAnchor, constant: 12),
            toggleButton.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 20),
            toggleButton.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -20),

            continueButton.topAnchor.constraint(equalTo: toggleButton.bottomAnchor, constant: 10),
            continueButton.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 20),
            continueButton.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -20),
            continueButton.bottomAnchor.constraint(equalTo: containerView.safeAreaLayoutGuide.bottomAnchor, constant: -20)
        ])

        containerView.addSubview(activityIndicator)
        NSLayoutConstraint.activate([
            activityIndicator.centerXAnchor.constraint(equalTo: toggleButton.centerXAnchor),
            activityIndicator.centerYAnchor.constraint(equalTo: toggleButton.centerYAnchor)
        ])
    }

    private func populate() {
        guard let attrs = attendee?.attributes else { return }

        nameLabel.text = attrs.fullName
        nameLabel.font = UIFont.systemFont(ofSize: 20, weight: .bold)

        emailLabel.text = attrs.email ?? "No email"
        emailLabel.font = UIFont.systemFont(ofSize: 14)
        emailLabel.textColor = .gray

        companyLabel.text = [attrs.jobTitle, attrs.company]
            .compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: " · ")
        companyLabel.font = UIFont.systemFont(ofSize: 14)
        companyLabel.textColor = .darkGray

        identifierLabel.text = "ID: \(attendee?.id ?? "—")"
        identifierLabel.font = UIFont.systemFont(ofSize: 12)
        identifierLabel.textColor = .lightGray

        refreshStatusUI()
    }

    private func refreshStatusUI() {
        if isCheckedIn {
            statusBanner.backgroundColor = UIColor.systemGreen
            statusLabel.text = "✓  Checked In"
            toggleButton.setTitle("Check Out", for: .normal)
            toggleButton.backgroundColor = UIColor.systemOrange
            toggleButton.setTitleColor(.white, for: .normal)
        } else {
            statusBanner.backgroundColor = UIColor.systemOrange
            statusLabel.text = "✗  Not Checked In"
            toggleButton.setTitle("Check In", for: .normal)
            toggleButton.backgroundColor = UIColor.systemGreen
            toggleButton.setTitleColor(.white, for: .normal)
        }
    }

    // MARK: - Animation

    private func animateIn() {
        containerView.transform = CGAffineTransform(translationX: 0, y: containerView.bounds.height + 100)
        UIView.animate(withDuration: 0.35, delay: 0, usingSpringWithDamping: 0.85,
                       initialSpringVelocity: 0.5, options: .curveEaseOut) {
            self.containerView.transform = .identity
        }
    }

    private func animateOut(completion: @escaping () -> Void) {
        UIView.animate(withDuration: 0.25, animations: {
            self.containerView.transform = CGAffineTransform(translationX: 0,
                                                             y: self.containerView.bounds.height + 100)
            self.view.backgroundColor = .clear
        }, completion: { _ in completion() })
    }

    // MARK: - Actions

    @objc private func toggleTapped() {
        guard let attendeeId = attendee?.id else { return }
        toggleButton.isEnabled = false
        toggleButton.setTitle("", for: .normal)
        activityIndicator.startAnimating()

        let newState = !isCheckedIn
        CheckInService.toggleCheckIn(attendeeId: attendeeId, isCheckedIn: newState) { [weak self] success, error in
            guard let self = self else { return }
            DispatchQueue.main.async {
                self.activityIndicator.stopAnimating()
                self.toggleButton.isEnabled = true
                if success {
                    self.isCheckedIn = newState
                    self.attendee?.attributes?.isCheckedIn = newState
                    self.refreshStatusUI()
                } else {
                    let alert = UIAlertController(title: "Error", message: error ?? "Unknown error",
                                                  preferredStyle: .alert)
                    alert.addAction(UIAlertAction(title: "OK", style: .default))
                    self.present(alert, animated: true)
                }
            }
        }
    }

    @objc private func continueTapped() {
        animateOut { [weak self] in
            guard let self = self else { return }
            self.dismiss(animated: false) {
                self.delegate?.confirmDidDismiss(self)
            }
        }
    }

    @objc private func backgroundTapped() {
        continueTapped()
    }
}
