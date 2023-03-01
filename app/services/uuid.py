import re
import uuid
import hashlib


def is_valid(uuid):
    """Validate the format of a uuid.

    Is intended to be valid if it respects
    its `canonical textual representation`
    defined in the RFC 4122.
    """
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    match = re.match(pattern, uuid)
    return True if match is not None else False


def uuidv4():
    return uuid.uuid4()


def generate_uuid_from_string(the_string, starting):
    """
    Returns String representation of the UUID of a hex md5 hash of the given string
    """
    # Instansiate new md5_hash
    md5_hash = hashlib.md5()

    the_string = starting + the_string
    # Pass the_string to the md5_hash as bytes
    md5_hash.update(the_string.encode("utf-8"))

    # Generate the hex md5 hash of all the read bytes
    the_md5_hex_str = md5_hash.hexdigest()

    # Return a String repersenation of the uuid of the md5 hash
    return str(uuid.UUID(the_md5_hex_str))
