import re
import logging


def validate(data, accepted_keys, accepted_values):
    """Validate generic data dictionary.

        It makes use of a list of the accepted keys
        in the dictionary, and another dictionary
        containing for each key the regex to validate
        the respective values.
    """
    logging.debug("[VALIDATION]")
    validated = {}
    for key in data:
        if key in accepted_keys:
            logging.debug(f"Now validating: {key}")
            value = data[key]
            bingo = re.match(accepted_values[key], value)
            if bingo is not None:
                validated[key] = value
    logging.debug(f"\n[VALIDATED]\n {validated.keys()}")
    return validated
