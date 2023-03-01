from services.core import validator
import json


def validate_mngmnt_users_modify(data):
    """Validate input data for users modify request.

    A user  has been request to be modified
    and a validation process is needed. Here is defined
    the logics for those checks, and a services core lib
    is used to perform low-level checks.
    """
    accepted_keys = ["password"]
    accepted_values = {"password": r"^.{8,32}$"}
    data = json.loads(json.dumps(data), parse_int=str)
    return validator.validate(data, accepted_keys, accepted_values)


def validate_update(data):
    """Validate input data for instance update request.

    A workflow instance has been request to be updated
    and a validation process is needed. Here is defined
    the logics for those checks, and a services core lib
    is used to perform low-level checks.
    """
    accepted_keys = ["state"]
    accepted_values = {"state": r"^0$|^2$"}
    data = json.loads(json.dumps(data), parse_int=str)
    return validator.validate(data, accepted_keys, accepted_values)