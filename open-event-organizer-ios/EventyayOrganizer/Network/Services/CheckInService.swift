//
//  CheckInService.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import Alamofire
import Foundation

class CheckInService {

    /// PATCH /v1/attendees/{id} — toggle is-checked-in and record timestamp.
    static func toggleCheckIn(attendeeId: String,
                              isCheckedIn: Bool,
                              completion: @escaping (Bool, String?) -> Void) {
        guard let token = KeychainHelper.get(key: "jwt_token") else {
            completion(false, "Not authenticated")
            return
        }
        let urlString = "\(APIClient.shared.kBaseURL)/attendees/\(attendeeId)"
        guard let url = URL(string: urlString) else {
            completion(false, "Invalid URL")
            return
        }

        let timestamp = ISO8601DateFormatter().string(from: Date())

        // JSON:API PATCH body
        var attributes: [String: Any] = ["is-checked-in": isCheckedIn]
        if isCheckedIn {
            attributes["checkin-times"] = timestamp
            attributes["device-name-checkin"] = "iOS-App"
        }
        let body: [String: Any] = [
            "data": [
                "type": "attendee",
                "id": attendeeId,
                "attributes": attributes
            ]
        ]

        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue("application/vnd.api+json", forHTTPHeaderField: "Content-Type")
        request.setValue("JWT \(token)", forHTTPHeaderField: "Authorization")

        guard let data = try? JSONSerialization.data(withJSONObject: body) else {
            completion(false, "Serialization error")
            return
        }
        request.httpBody = data

        Alamofire.request(request).response { response in
            if let statusCode = response.response?.statusCode, statusCode == 200 {
                completion(true, nil)
            } else {
                let msg = response.error?.localizedDescription ?? "Check-in failed (HTTP \(response.response?.statusCode ?? 0))"
                completion(false, msg)
            }
        }
    }
}
