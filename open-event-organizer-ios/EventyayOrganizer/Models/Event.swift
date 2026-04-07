//
//  Event.swift
//  EventyayOrganizer
//
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import Foundation
import ObjectMapper

class EventAttributes: Mappable {
    var name: String?
    var startsAt: String?
    var endsAt: String?
    var state: String?
    var description: String?
    var identifier: String?

    required init?(map: Map) {}

    func mapping(map: Map) {
        name <- map["name"]
        startsAt <- map["starts-at"]
        endsAt <- map["ends-at"]
        state <- map["state"]
        description <- map["description"]
        identifier <- map["identifier"]
    }
}

class EventData: Mappable {
    var id: String?
    var attributes: EventAttributes?

    required init?(map: Map) {}

    func mapping(map: Map) {
        id <- map["id"]
        attributes <- map["attributes"]
    }
}

class EventsResponse: Mappable {
    var data: [EventData]?

    required init?(map: Map) {}

    func mapping(map: Map) {
        data <- map["data"]
    }
}
