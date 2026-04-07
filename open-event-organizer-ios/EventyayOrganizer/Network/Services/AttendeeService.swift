//
//  AttendeeService.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import Alamofire
import AlamofireObjectMapper
import Foundation

class AttendeeService {
    static func fetchAttendees(eventId: String,
                               completion: @escaping ([AttendeeData]) -> Void) {
        guard let token = KeychainHelper.get(key: "jwt_token") else {
            completion([])
            return
        }
        let urlString = "\(APIClient.shared.kBaseURL)/events/\(eventId)/attendees?page[size]=100&sort=firstname"
        guard let url = URL(string: urlString) else {
            completion([])
            return
        }
        var request = URLRequest(url: url)
        request.setValue("JWT \(token)", forHTTPHeaderField: "Authorization")

        Alamofire.request(request).responseObject { (response: DataResponse<AttendeesResponse>) in
            completion(response.value?.data ?? [])
        }
    }
}
