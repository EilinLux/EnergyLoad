from services.core.auth import JwtSessionExpired
from controller.user import User
from handler.routers.users import UsersRouter
from handler.routers.services import ServicesRouter
from services.auth import Auth
from services.monitoring import Event

from flask import request, Response
import os
import logging
import traceback

_ESP_URL = os.environ.get("_ESP_URL")
_PROJECT_ID = os.environ.get("_PROJECT_ID")
_SERVICE_ACCOUNT_JWT_SECRET = os.environ.get("_SERVICE_ACCOUNT_JWT_SECRET") 
_CLOUD_SQL_INSTANCE_CONNECTION_NAME = os.environ.get("_CLOUD_SQL_INSTANCE_CONNECTION_NAME")
_MAIN_DB_SECRET = os.environ.get("_MAIN_DB_SECRET")


class Router:
    def __init__(self, app, local_secret_store):
        self.app = app
        self.local_secret_store = local_secret_store

        @app.route('/health', methods=['GET'])
        def health():
            """Return a friendly smile to express the status of the service."""
            return ':-)'

        @app.route('/login', methods=['POST'])
        def login():
            """Allow a user to log in."""
            log = Event(request, self.local_secret_store)
            body = request.get_json()
            logging.debug("Body Received")
            logging.debug(body)

            try:
                logging.info("Handling POST on /login...")
                auth_manager = Auth(_PROJECT_ID, _SERVICE_ACCOUNT_JWT_SECRET,
                                    _ESP_URL, _MAIN_DB_SECRET,
                                    _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                    self.local_secret_store)
                # event 
                return log.create_event(auth_manager.login(body))

            except Exception as e:
                logging.error(e)
                logging.error(traceback.format_exc())
                return log.create_event(Response("internal server error", 500))

        @app.route('/logout', methods=['POST'])
        def logout():
            """Allow a user to log out."""
            log = Event(request, self.local_secret_store)

            session_token = request.headers.get('X-Endpoint-Api-Userinfo')

            try:
                logging.info("Handling POST on /logout...")
                auth_manager = Auth(_PROJECT_ID, _SERVICE_ACCOUNT_JWT_SECRET,
                                    _ESP_URL, _MAIN_DB_SECRET,
                                    _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                    self.local_secret_store)
                
                return log.create_event(auth_manager.logout(session_token))

            except Exception as e:
                logging.error(e)
                traceback.format_exc()
                return log.create_event(Response("internal server error", 500))

        @app.route('/user', methods=['GET'])
        def user_info():
            """Get user info."""
            log = Event(request, self.local_secret_store)

            try:
                logging.info("Handling GET on /user...")
                session_token = request.headers.get('X-Endpoint-Api-Userinfo')
                auth_manager = Auth(_PROJECT_ID, _SERVICE_ACCOUNT_JWT_SECRET,
                                    _ESP_URL, _MAIN_DB_SECRET,
                                    _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                                    local_secret_store)
                auth_manager.validate_jwt(session_token)
                return log.create_event(User(local_secret_store, session_token).get())

            except JwtSessionExpired as e:
                logging.error(e)
                response = Response("unauthorized", 401)
                response.headers["WWW-Authenticate"] = "Basic realm=/login"
                return log.create_event(response)

            except Exception as e:
                logging.error(e)
                logging.error(traceback.format_exc())
                return log.create_event(Response("internal server error", 500))

        UsersRouter(app, local_secret_store)
        ServicesRouter(app, local_secret_store)
