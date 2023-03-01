import requests
import json
import os 
import traceback
_GET_ACCESS_TOKEN = os.environ.get("_GET_ACCESS_TOKEN")
_GET_SITE_ID = os.environ.get("_GET_SITE_ID")
_GET_METER_ID = os.environ.get("_GET_METER_ID")
_POST_JSON_CONSUMPTION = os.environ.get("_POST_JSON_CONSUMPTION")


class AccessTokenException(Exception):
    """Exception for the e-sight session."""

    def __init__(self, message):
        super().__init__(message)

class MeterIdListException(Exception):
    """Exception for the e-sight session."""

    def __init__(self, message):
        super().__init__(message)

class SiteIdListException(Exception):
    """Exception for the e-sight session."""

    def __init__(self, message):
        super().__init__(message)


class SendingToESightException(Exception):
    """Exception for the e-sight session."""

    def __init__(self, message):
        super().__init__(message)

def get_access_token(
    Username,
    Password,
    request_token_url=_GET_ACCESS_TOKEN
):
    try: 
        request_token = requests.get(request_token_url, auth=(Username, Password))
        access_token = json.loads(request_token.text)["access_token"]
        return access_token
    except: 
        raise AccessTokenException(traceback.format_exc())

def list_siteid(
        access_token,
        url=_GET_SITE_ID
):
    try:
        print("Collecting site_id list...")

        headers = {}  # CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = "Bearer {}".format(access_token)

        resp = requests.get(url, headers=headers)
        data = json.loads(resp.text)
        result = [json.dumps(record) for record in data]
        site_code_list = []
        for i in range(len(result)):
            site_code_list.append(json.loads(result[i]).get("SiteCode"))

        return site_code_list
    except:
        raise SiteIdListException(traceback.format_exc())

def list_meterid(
        access_token,
        url=_GET_METER_ID
):
    
    try:
        print("Collecting meter_id list...")

        headers = {}  # CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = "Bearer {}".format(access_token)

        resp = requests.get(url, headers=headers)
        data = json.loads(resp.text)
        result = [json.dumps(record) for record in data]
        meter_code_list = []
        for i in range(len(result)):
            meter_code_list.append(json.loads(result[i]).get("MeterCode"))

        return meter_code_list
    except:
        raise MeterIdListException(traceback.format_exc())

# API to send data to e-sight


def send_to_e_sight_dev(
    result_json,
    post_Username,
    post_Password,
    post_url=_POST_JSON_CONSUMPTION
):
    try: 
        print("Sending request to E-Sight...")
        request = requests.post(post_url,
                                json=result_json,
                                auth=(post_Username, post_Password))
        return request.status_code
    except: 
        return SendingToESightException(f"Exception on sending error: \n{traceback.format_exc()}")