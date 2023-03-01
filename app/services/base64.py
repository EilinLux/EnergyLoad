import base64 as b64


def b64decode(string):
    """Decode base64 to string."""
    try:
        return b64.b64decode(string)
    except:
        return ""


def decode_base64(string, padding=b'==='):
    """Decode base64, considering padding.
    
    Notes:
        This function consider the possibility to 
        have an input string with incorrect padding:
        https://stackoverflow.com/a/49459036/6113317
    
    Args:
        string (str), the ASCII-like string to decode.
    
    Returns:
        decoded (str), the decoded ASCII-like string.
    """

    bytestring = string.encode('utf-8')
    bytedecoded = b64.b64decode(bytestring + padding)
    decoded = bytedecoded.decode('utf-8')
    return decoded


def encode_base64(string):
    """Base64 encode."""
    return str(b64.encodebytes(string).decode("utf-8"))
