//
//  EventService.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import Alamofire
import AlamofireObjectMapper
import Foundation

class EventService {
    static func fetchEvents(completion: @escaping ([EventData]) -> Void) {
        guard let token = KeychainHelper.get(key: "jwt_token") else {
            completion([])
            return
        }
        let urlString = "\(APIClient.shared.kBaseURL)/events?page[size]=50&sort=starts-at"
        guard let url = URL(string: urlString) else {
            completion([])
            return
        }
        var request = URLRequest(url: url)
        request.setValue("JWT \(token)", forHTTPHeaderField: "Authorization")

        Alamofire.request(request).responseObject { (response: DataResponse<EventsResponse>) in
            completion(response.value?.data ?? [])
        }
    }
}
