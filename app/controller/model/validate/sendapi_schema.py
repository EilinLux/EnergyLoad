send_api_jsonSchema = {
    "type": "object",
    "properties": {
        "messageType": {"type": "string"},
        "header": {"type": "object"},
        "gatewayData": {"type": "object"},
    },
    "required": ["messageType", "header", "gatewayData"]
}
