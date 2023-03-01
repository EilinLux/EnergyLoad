send_errors_config = {
    "NoSiteId": {
        "name": "NoSiteId",
        "message": "SiteId not existing on e-sight."
    },
    "NoMeterId": {
        "name": "NoMeterId",
        "message": "MeterId not existing on e-sight."
    },
    "InvalidJson": {
        "name": "InvalidJson",
        "message": "An invalid Json has been sent to e-sight, please check the schema."
    },    
    "InvalidJsonReceived": {
        "name": "InvalidJson",
        "message": "An invalid Json has been sent from e-sight."
    },    
    "EmptyJson": {
        "name": "EmptyJson",
        "message": "No Json has been sent from e-sight in the body."
    },
    "MalformedMessage_id": {
        "name": "MalformedMessage_id",
        "message": "Malformed message_id, not able to retrieve data_feed_type"
    },
        "MalformedMessage_id": {
        "name": "MalformedMessage_id",
        "message": "Malformed message_id, not able to retrieve data_feed_type"
    },
    "200": {
        "name": "Success",
        "message": "Successfully sent the file  to e-Sight."
    },
    "400": {
        "name": "BadRequest",
        "message": "Cannot process the request because it is malformed or incorrect."
    },
    "401": {
        "name": "Unauthorized",
        "message": "Required authentication information is either missing or not valid for the resource."
    },
    "403": {
        "name": "Forbidden",
        "message": "Access is denied to the requested resource. The user might not have enough permission."
    },
    "404": {
        "name": "NotFound",
        "message": "The requested resource doesn't exist."
    },
    "405": {
        "name": "MethodNotAllowed",
        "message": "The HTTP method in the request is not allowed on the resource."
    },
    "406": {
        "name": "NotAcceptable",
        "message": "This service doesn't support the format requested in the Accept header."
    },
    "409": {
        "name": "Conflict",
        "message": "The current state conflicts with what the request expects."
    },
    "410": {
        "name": "Gone",
        "message": "The requested resource is no longer available at the server."
    },
    "411": {
        "name": "LengthRequired",
        "message": "A Content-Length header is required on the request."
    },
    "412": {
        "name": "PreconditionFailed",
        "message": "A precondition provided in the request (such as an if-match header) does not match the resource's current state."
    },
    "413": {
        "name": "RequestEntityTooLarge",
        "message": "The request size exceeds the maximum limit."
    },
    "415": {
        "name": "UnsupportedMediaType",
        "message": "The content type of the request is a format that is not supported by the service."
    },
    "416": {
        "name": "RequestedRangeNotSatisfiable",
        "message": "The specified byte range is invalid or unavailable."
    },
    "422": {
        "name": "UnprocessableEntity",
        "message": "Cannot process the request because it is semantically incorrect."
    },
    "423": {
        "name": "Locked",
        "message": "The resource that is being accessed is locked."
    },
    "429": {
        "name": "TooManyRequests",
        "message": "Client application has been throttled and should not attempt to repeat the request until an amount of time has elapsed."
    },
    "500": {
        "name": "InternalServerError",
        "message": "There was an internal server error while processing the request."
    },
    "501": {
        "name": "NotImplemented",
        "message": "The requested feature isn't implemented."
    },
    "503": {
        "name": "ServiceUnavailable",
        "message": "The service is temporarily unavailable for maintenance or is overloaded. You may repeat the request after a delay, the length of which may be specified in a Retry-After header."
    },
    "504": {
        "name": "GatewayTimeout",
        "message": "The server, while acting as a proxy, did not receive a timely response from the upstream server it needed to access in attempting to complete the request. May occur together with 503."
    },
    "507": {
        "name": "InsufficientStorage",
        "message": "The maximum storage quota has been reached."
    },
    "509": {
        "name": "BandwidthLimitExceeded",
        "message": "Your app has been throttled for exceeding the maximum bandwidth cap. Your app can retry the request again after more time has elapsed."
    }
}
