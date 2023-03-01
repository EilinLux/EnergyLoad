from controller.user import User
from services import auth
from services.core.auth import JwtSessionExpired

from flask import Flask, request, Response
import logging
import os
import traceback

_ESP_URL = os.environ.get("_ESP_URL")
_PROJECT_ID = os.environ.get("_PROJECT_ID")
_SERVICE_ACCOUNT_JWT_SECRET = os.environ.get("_SERVICE_ACCOUNT_JWT_SECRET") 
_CLOUD_SQL_INSTANCE_CONNECTION_NAME = os.environ.get("_CLOUD_SQL_INSTANCE_CONNECTION_NAME")
_MAIN_DB_SECRET = os.environ.get("_MAIN_DB_SECRET")

class AuthRouter(object):
    def __init__(self, app, local_secret_store):
        self.app = app
        self.local_secret_store = local_secret_store

        @app.route('/login', methods=['POST'])
        def login():
            """Allow a user to log in."""

            body = request.get_json()
            logging.debug("Body Received")
            logging.debug(body)

            try:
                logging.info("Handling POST on /login...")
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                return auth_manager.login(body)

            except Exception as e:
                logging.error(e)
                traceback.format_exc()
                return Response("internal server error", 500)

        @app.route('/user', methods=['GET'])
        def user_info():
            """Get user info."""

            try:
                logging.info("Handling GET on /user...")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                auth_manager.validate_jwt(session_token)
                return User(local_secret_store, session_token).get()

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return response

            except Exception as e:
                logging.error(e)
                traceback.format_exc()
                return Response("internal server error", 500)

        @app.route('/logout', methods=['POST'])
        def logout():
            """Allow a user to log out."""

            try:
                logging.info("Handling POST on /logout...")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                auth_manager = auth.Auth(_PROJECT_ID,
                                         _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL,
                                         _MAIN_DB_SECRET,
                                         _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                         local_secret_store)
                auth_manager.validate_jwt(session_token)
                return auth_manager.logout(session_token)

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return response

            except Exception as e:
                logging.error(e)
                traceback.format_exc()
                return Response("internal server error", 500)
