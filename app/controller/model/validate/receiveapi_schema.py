receive_api_jsonSchema = {
    "type": "object",
    "properties": {
        "_id": {
            "type": "string"
        },
        "header": {
            "type": "object"
        },
        "errors": {
            "type": "array"
        },
    },
    "required": ["_id", "header", "errors"]
}
