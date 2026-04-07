//
//  LoginResponse.swift
//  EventyayOrganizer
//
//  Created for KHSC iOS login implementation.
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import Foundation
import ObjectMapper

class LoginResponse: Mappable {
    var accessToken: String?
    var error: String?

    init() {}

    required init?(map: Map) {}

    func mapping(map: Map) {
        accessToken <- map["access_token"]
        error <- map["error"]
    }
}
