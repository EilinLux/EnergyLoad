from enum import Enum

nodes = {
    "START": "startEvent",
    "EXCLUSIVE_GATEWAY": "exclusiveGateway",
    "SCRIPT_TASK": "scriptTask",
    "USER_TASK": "userTask",
    "END": "endEvent"
}

workflow_states = {"DRAFT": 0, "PUBLISHED": 1, "DELETED": 2, "ASSOCIATED": 3}

instance_states = {
    "COMPLETED": 0,
    "RUNNING": 1,
    "CANCELED": 2,
    "TO_BE_FILLED": 3,
    "SYNC_RUNNING": 4,
    "REVIEWED": 7,
    "COMPLETED_ARCHIVED": 1000,
    "RUNNING_ARCHIVED": 1001,
    "CANCELED_ARCHIVED": 1002,
    "TO_BE_FILLED_ARCHIVED": 1003
}

users_type = {"admin": "admin", "backoffice": "backoffice", "user": "user"}

users_tables_name = {
    "admin": "admin_users",
    "backoffice": "backoffice_users",
    "user": "users"
}

entity_types = {"CITY": 1, "PROVINCE": 2, "CAP": 3}

area_workflow_association_states = {"ACTIVE": 1, "INACTIVE": 0}


class EndEvent():
    class type():
        MESSAGE = "message"
        SUMMARY = "summary"


class UserTask():
    class action():
        NEXT = "NEXT"
        PREVIOUS = "PREVIOUS"
