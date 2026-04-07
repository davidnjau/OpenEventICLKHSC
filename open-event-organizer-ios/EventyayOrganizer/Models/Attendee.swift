//
//  Attendee.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import Foundation
import ObjectMapper

class AttendeeAttributes: Mappable {
    var firstname: String?
    var lastname: String?
    var email: String?
    var phone: String?
    var company: String?
    var jobTitle: String?
    var gender: String?
    var city: String?
    var state: String?
    var country: String?
    var address: String?
    var identifier: String?
    var isCheckedIn: Bool?
    var checkinTimes: String?
    var deviceNameCheckin: String?

    required init?(map: Map) {}

    func mapping(map: Map) {
        firstname <- map["firstname"]
        lastname <- map["lastname"]
        email <- map["email"]
        phone <- map["phone"]
        company <- map["company"]
        jobTitle <- map["job-title"]
        gender <- map["gender"]
        city <- map["city"]
        state <- map["state"]
        country <- map["country"]
        address <- map["address"]
        identifier <- map["identifier"]
        isCheckedIn <- map["is-checked-in"]
        checkinTimes <- map["checkin-times"]
        deviceNameCheckin <- map["device-name-checkin"]
    }

    var fullName: String {
        let parts = [firstname, lastname].compactMap { $0 }.filter { !$0.isEmpty }
        return parts.isEmpty ? "Unknown" : parts.joined(separator: " ")
    }
}

class AttendeeData: Mappable {
    var id: String?
    var attributes: AttendeeAttributes?

    required init?(map: Map) {}

    func mapping(map: Map) {
        id <- map["id"]
        attributes <- map["attributes"]
    }
}

class AttendeesResponse: Mappable {
    var data: [AttendeeData]?
    var meta: AttendeeMeta?

    required init?(map: Map) {}

    func mapping(map: Map) {
        data <- map["data"]
        meta <- map["meta"]
    }
}

class AttendeeMeta: Mappable {
    var count: Int?

    required init?(map: Map) {}

    func mapping(map: Map) {
        count <- map["count"]
    }
}
