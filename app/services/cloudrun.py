import json
import logging
import requests
import os

ENV = os.environ.get("ENVIRONMENT", "remote")
CLOUD_RUN_ID_TOKEN = os.environ.get("CLOUD_RUN_ID_TOKEN", None)


def send_request(method, url, parameters=None, body=None):
    """Send a REST request to a cloud run service.

    Args:
        method (str): the rest method.
        url (str): the url to call.
        parameters(dict): the query string parameters.
        body(dict): the body for the request.

    Returns:
        response (requests.Response): the response object.
    """

    # If query string parameters specified
    query_string_paremeters = ''
    if parameters is not None:
        # Transform the parameters dict to a string
        # Format: ?key1=value1&key2=value2&....
        query_string_paremeters = '?' + '&'.join(
            [key + "=" + str(parameters[key]) for key in parameters])

    # Add query string parameters (if any)
    receiving_service_url = url
    receiving_service_url += query_string_paremeters

    # Print info
    logging.info(
        f"[INFO] Dispatching {method} request to: {receiving_service_url}, with body: {body}."
    )

    # Prepare the request and invoke the endpoint selected
    try:

        if ENV == "local":
            # TODO capire come ottenere da application defualt l'id token
            # https://cloud.google.com/run/docs/authenticating/developers#console-ui
            # https://google-auth.readthedocs.io/en/latest/user-guide.html  --> Identity Tokens
            # comando per generare il token tramite application default credential--> gcloud auth print-identity-token
            receiving_service_headers = {'Authorization': f'bearer {CLOUD_RUN_ID_TOKEN}'}
            requests.get(url=receiving_service_url, headers=receiving_service_headers)
        else:
            # Set the endpoint for the Google Metadata Server
            metadata_server_token_url = 'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience='
            token_request_url = metadata_server_token_url + receiving_service_url
            token_request_headers = {'Metadata-Flavor': 'Google'}

            # Fetch the token
            token_response = requests.get(token_request_url,
                                          headers=token_request_headers)
            jwt = token_response.content.decode("utf-8")

            # Provide the token in the request to the receiving service
            receiving_service_headers = {'Authorization': f'bearer {jwt}'}
            requests.get(url=receiving_service_url,
                         headers=receiving_service_headers)

    except Exception as e:
        logging.exception(e)
        raise e
