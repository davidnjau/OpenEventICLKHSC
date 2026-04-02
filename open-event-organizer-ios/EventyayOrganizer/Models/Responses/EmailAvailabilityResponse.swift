//
//  EmailAvailabilityResponse.swift
//  EventyayOrganizer
//
//  Created by Dilum De Silva on 4/3/19.
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import Foundation
import ObjectMapper

class EmailAvailabilityResponse: Mappable {
    // Server returns {"exists": true/false}
    // exists=true  → email taken  → isAvailable=false → navigate to Login
    // exists=false → email free   → isAvailable=true  → navigate to SignUp
    private var exists: Bool?
    var error: String?
    var isAvailable: Bool? {
        guard let exists = exists else { return nil }
        return !exists
    }

    init() {}

    required init?(map: Map) {
        exists <- map["exists"]
        error <- map["error"]
    }

    func mapping(map: Map) {
        exists <- map["exists"]
        error <- map["error"]
    }
}
