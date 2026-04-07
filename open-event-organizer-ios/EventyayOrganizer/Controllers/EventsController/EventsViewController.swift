//
//  EventsViewController.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import UIKit

class EventsViewController: UITableViewController {

    private var events: [EventData] = []
    private let cellIdentifier = "EventCell"

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Events"
        navigationItem.rightBarButtonItem = UIBarButtonItem(
            title: "Logout",
            style: .plain,
            target: self,
            action: #selector(logoutTapped)
        )
        tableView.register(UITableViewCell.self, forCellReuseIdentifier: cellIdentifier)
        loadEvents()
    }

    private func loadEvents() {
        EventService.fetchEvents { [weak self] events in
            DispatchQueue.main.async {
                self?.events = events
                self?.tableView.reloadData()
            }
        }
    }

    @objc private func logoutTapped() {
        KeychainHelper.delete(key: "jwt_token")
        navigationController?.popToRootViewController(animated: true)
    }

    // MARK: - UITableViewDataSource

    override func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return events.isEmpty ? 1 : events.count
    }

    override func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: cellIdentifier, for: indexPath)
        if events.isEmpty {
            cell.textLabel?.text = "No events found"
            cell.detailTextLabel?.text = nil
            cell.accessoryType = .none
            return cell
        }
        let event = events[indexPath.row]
        cell.textLabel?.text = event.attributes?.name ?? "Unnamed Event"
        cell.detailTextLabel?.text = event.attributes?.startsAt ?? event.attributes?.state ?? ""
        cell.accessoryType = .disclosureIndicator
        return cell
    }

    override func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
        return 60
    }
}
