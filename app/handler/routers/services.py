from services import auth
from services.core.auth import JwtSessionExpired
from controller.services.sendjson import SendJsons
from controller.services.receivejson import ReceiveErrorJson
from services.monitoring import Event

from flask import request, Response
import logging
import os
import traceback


_ESP_URL = os.environ.get("_ESP_URL")
_PROJECT_ID = os.environ.get("_PROJECT_ID")
_SERVICE_ACCOUNT_JWT_SECRET = os.environ.get("_SERVICE_ACCOUNT_JWT_SECRET") 
_CLOUD_SQL_INSTANCE_CONNECTION_NAME = os.environ.get("_CLOUD_SQL_INSTANCE_CONNECTION_NAME")
_MAIN_DB_SECRET = os.environ.get("_MAIN_DB_SECRET")

class ServicesRouter(object):
    def __init__(self, app, local_secret_store):
        self.app = app
        self.local_secret_store = local_secret_store

        # ====================================================================
        # SERVICE SEND JSON (all)
        # ====================================================================

        @app.route('/api/v1/service/send/sendJsons', methods=['POST'])
        def send_all_jsons():
            """send all files to e-sight."""
            log = Event(request, self.local_secret_store)

            try:

                # Check authentication
                logging.info(f"Handling GET on /api/v1/services/sendJsons...")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                logging.info(session_token)
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                auth_manager.validate_jwt(session_token)

                # Demand the request to the controller layer
                return log.create_event(SendJsons(local_secret_store,
                                 session_token).send_files_to_e_sight())

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return log.create_event(response)

            except Exception as e:
                logging.error(e)
                logging.error(traceback.format_exc())
                return log.create_event(Response("internal server error", 500))

        # ====================================================================
        # SERVICE SEND JSON (single file)
        # ====================================================================

        @app.route('/api/v1/service/send/sendJson/<file_name>', methods=['GET'])
        def send_json(file_name):
            """send a single files to e-sight using its name on CloudStorage."""
            log = Event(request, self.local_secret_store)

            try:

                # Check authentication
                logging.info(f"Handling GET on /api/v1/services/sendJsons...")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                logging.info(session_token)
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                auth_manager.validate_jwt(session_token)

                # Demand the request to the controller layer
                return log.create_event(SendJsons(local_secret_store,
                                 session_token).send_files_to_e_sight(file_name))

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return log.create_event(response)

            except Exception as e:
                logging.error(e)
                logging.error(traceback.format_exc())
                return log.create_event(Response("internal server error", 500))

        # ====================================================================
        # SERVICE RECEIVE JSON (all)
        # ====================================================================

        @app.route('/api/v1/service/receive/errorjson', methods=['POST'])
        def receive_errorjson():
            """Receive error json file from e-sight."""
            log = Event(request, self.local_secret_store)

            try:

                # Check authentication
                logging.info(
                    f"Handling POST on /api/v1/service/receive/errorjson...")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                logging.info(session_token)
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                auth_manager.validate_jwt(session_token)

                # Demand the request to the controller layer
                return log.create_event(ReceiveErrorJson(
                    local_secret_store,
                    session_token).receive_error_json_from_e_sight())

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return log.create_event(response)

            except Exception as e:
                logging.error(e)
                logging.error(traceback.format_exc())
                return log.create_event(Response("internal server error", 500))

