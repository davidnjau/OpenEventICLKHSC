//
//  UserService.swift
//  EventyayOrganizer
//
//  Created by Dilum De Silva on 4/3/19.
//  Copyright © 2019 FOSSAsia. All rights reserved.
//

import Alamofire
import AlamofireObjectMapper
import Foundation
import ObjectMapper

class UserService {
    static let serverError = "{\"error\":\"Oops.. Something went wrong at the server. Please try again!\"}"
    static let emailValidationError = "{\"error\":\"Email validation request failed!\"}"
    static let genericError = "{\"error\":\"Oops.. Something went wrong. Please try again!\"}"
    private init() {}

    public static func checkEmailAvailability(_ email: String,
                                              completion: @escaping (EmailAvailabilityResponse) -> Void) {
        do {
            try APIClient.shared.post(ControllerConstants.CommonURL.checkEmail,
                                      withParams: ["email": email],
                                      type: EmailAvailabilityResponse()) { urlResponse, result, _ in
                switch urlResponse?.statusCode {
                case 422, 200:
                    completion(result!)
                default:
                    let emailAvailabilityResponseObj = EmailAvailabilityResponse(JSONString: serverError)
                    completion(emailAvailabilityResponseObj!)
                }
            }
        } catch APIClientError.jsonSerializationError {
            let emailAvailabilityResponseObj = EmailAvailabilityResponse(JSONString: emailValidationError)
            completion(emailAvailabilityResponseObj!)
        } catch {
            let emailAvailabilityResponseObj = EmailAvailabilityResponse(JSONString: genericError)
            completion(emailAvailabilityResponseObj!)
        }
    }

    public static func signup(_ email: String, completion: @escaping () -> Void) {}

    public static func login(_ email: String,
                             password: String,
                             completion: @escaping (LoginResponse) -> Void) {
        // The auth endpoint is at /auth/session (outside of /v1), so resolve as a relative URL
        guard let baseURL = URL(string: APIClient.shared.kBaseURL + "/"),
              let authURL = URL(string: ControllerConstants.CommonURL.loginUser,
                               relativeTo: baseURL) else {
            completion(LoginResponse(JSONString: serverError)!)
            return
        }
        var urlRequest = URLRequest(url: authURL.absoluteURL)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let params: [String: Any] = ["email": email, "password": password]
        guard let body = try? JSONSerialization.data(withJSONObject: params) else {
            completion(LoginResponse(JSONString: serverError)!)
            return
        }
        urlRequest.httpBody = body
        Alamofire.request(urlRequest).responseObject { (response: DataResponse<LoginResponse>) in
            guard let loginResponse = response.value else {
                completion(LoginResponse(JSONString: serverError)!)
                return
            }
            if let token = loginResponse.accessToken {
                KeychainHelper.save(key: "jwt_token", value: token)
            }
            completion(loginResponse)
        }
    }
}
