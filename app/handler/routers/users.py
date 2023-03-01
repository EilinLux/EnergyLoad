from controller.management import users
from services import auth
from services.core.auth import JwtSessionExpired
from services.monitoring import Event

from flask import Flask, request, Response
import logging
import os
import traceback

_ESP_URL = os.environ.get("_ESP_URL")
_PROJECT_ID = os.environ.get("_PROJECT_ID")
_SERVICE_ACCOUNT_JWT_SECRET = os.environ.get("_SERVICE_ACCOUNT_JWT_SECRET") #"jwt_account"
_CLOUD_SQL_INSTANCE_CONNECTION_NAME = os.environ.get("_CLOUD_SQL_INSTANCE_CONNECTION_NAME")
_MAIN_DB_SECRET = os.environ.get("_MAIN_DB_SECRET")

class UsersRouter(object):
    def __init__(self, app, local_secret_store):
        self.app = app
        self.local_secret_store = local_secret_store

        @app.route('/api/v1/management/users/user', methods=['POST'])
        def create_user():
            """Create an end-user."""
            log = Event(request, self.local_secret_store)

            body = request.get_json()

            try:

                # Check authentication
                logging.info(f"Handling POST on /management/users/user")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                auth_manager.validate_jwt(session_token)

                # Demand the request to the controller layer
                return log.create_event(users.create(session_token, type="user",
                                    user=body,
                                    local_secret_store=local_secret_store))

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return log.create_event(response)

            except Exception as e:
                logging.error(e)
                traceback.format_exc()
                return log.create_event(Response("internal server error", 500))


        @app.route('/api/v1/management/users/user/edit/<id>', methods=['PATCH'])
        def modify_user(id):
            """Modify a user."""
            log = Event(request, self.local_secret_store)

            body = request.get_json()

            try:

                # Validate
                if id is None or body is None:
                    return Response("bad request", 400)

                # Check authentication
                logging.info("Handling POST on /management/users...")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                auth_manager.validate_jwt(session_token)

                # Demand the request to the controller layer
                return users.modify(type="backoffice",
                                    user_id=id,
                                    data=body,
                                    local_secret_store=local_secret_store)

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return log.create_event(response)

            except Exception as e:
                logging.error(e)
                traceback.format_exc()
                return log.create_event(Response("internal server error", 500))

        @app.route('/api/v1/management/users/user/deactivate/<id>', methods=['DELETE'])
        def deactivate_user(id):
            """Delete an end-user."""
            log = Event(request, self.local_secret_store)


            try:

                # Validate
                if id is None:
                    return Response("bad request", 400)

                # Check authentication
                logging.info("Handling POST on /management/users...")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                auth_manager.validate_jwt(session_token)

                # Demand the request to the controller layer
                return log.create_event(users.deactivate(id, local_secret_store))

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return log.create_event(response)

            except Exception as e:
                logging.error(e)
                traceback.format_exc()
                return log.create_event(Response("internal server error", 500))
