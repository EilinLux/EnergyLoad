from .core.auth import Jwt, JwtSessionExpired
from services.cloudsql import CloudSql
from services.base64 import decode_base64
from flask import Response
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
import json
import logging


class Auth():
    def __init__(self,
                 _PROJECT_ID,
                 _SERVICE_ACCOUNT_JWT_SECRET,
                 _ESP_URL,
                 _MAIN_DB_SECRET,
                 _CLOUD_SQL_INSTANCE_CONNECTION_NAME,
                 LOCAL_SECRET_STORE,
                 _DEFAULT_ENCODING='utf8'):
        self._DEFAULT_ENCODING = _DEFAULT_ENCODING
        self._PROJECT_ID = _PROJECT_ID
        self._SERVICE_ACCOUNT_JWT_SECRET = _SERVICE_ACCOUNT_JWT_SECRET
        self._ESP_URL = _ESP_URL
        self._MAIN_DB_SECRET = _MAIN_DB_SECRET
        self._CLOUD_SQL_INSTANCE_CONNECTION_NAME = _CLOUD_SQL_INSTANCE_CONNECTION_NAME
        self.local_secret_store = LOCAL_SECRET_STORE

    def login(self, req):
        """Perform login."""
        database_connection = None

        # Extract parameters
        username = req.get("username")
        password = req.get("password")

        # Validate
        if username is None or password is None:
            logging.info('Malformed input.')
            return Response("bad request", 400)

        try:

            # Connection to database
            logging.info('Connecting to MySQL DB...')
            db_user = self.local_secret_store[self._MAIN_DB_SECRET]["username"]
            db_password = self.local_secret_store[
                self._MAIN_DB_SECRET]["password"]
            database_connection = CloudSql().connect(
                self._CLOUD_SQL_INSTANCE_CONNECTION_NAME, db_user, db_password)

            logging.info('Query MySQL DB using the username and password provided in /login API body...')

            with database_connection.cursor() as cursor:
                sql_statement = """
                    SELECT bu.id, bu.password, bu.type
                    FROM `edm-db-workflows`.backoffice_users AS bu
                    WHERE bu.username = %s and bu.status = "active"
                    """

                cursor.execute(sql_statement, (username, ))
                user = cursor.fetchone()

                # Manage the case the user is not in the database
                if user is None:
                    logging.info('User not found.')
                    return Response("bad request", 400)

                # Verify the password
                ph = PasswordHasher()
                logging.info("Verifing password in /login API with the one store on MySQL")
                
                if ph.verify(user['password'], password):
                    logging.info('Verified password.')

                    jwt_manager = Jwt(self.local_secret_store, self._PROJECT_ID,
                                    self._SERVICE_ACCOUNT_JWT_SECRET,
                                    self._ESP_URL)

                    types = user['type'].split(",")
                    logging.info('Generating JWT...')

                    jwt = jwt_manager.generate(data={
                        'user_id': user['id'],
                        "allowed_for": types
                    }).decode(self._DEFAULT_ENCODING)

                    # TODO sent to SQL a record on login
                    return Response(jwt, 200, mimetype="text/plain")

        except VerifyMismatchError as e:
            logging.info('User provided wrong password.')
            return Response("bad request", 400)

        except VerificationError as e:
            logging.info('VerificationError.')
            return Response("bad request", 400)

        except Exception as e:
            logging.info(f'Exception occurred: {e}')
            raise Exception(e)

        finally:
            if database_connection is not None:
                database_connection.close()

    def logout(self, jwt):
        """Perform logout."""
        database_connection = None

        try:
            jwt_payload_decoded = decode_base64(jwt)
            payload = json.loads(jwt_payload_decoded)
            exp = payload.get("exp")

            db_user = self.local_secret_store[self._MAIN_DB_SECRET]["username"]
            db_password = self.local_secret_store[
                self._MAIN_DB_SECRET]["password"]
            database_connection = CloudSql().raw_connect(
                self._CLOUD_SQL_INSTANCE_CONNECTION_NAME, db_user, db_password)
            with database_connection.cursor() as cursor:
                sql_statement = """
                    INSERT INTO `edm-db-workflows`.backoffice_users_blacklist
                        VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE jwt = %s
                    """
                cursor.execute(sql_statement, (jwt, exp, jwt))
                database_connection.commit()
                return Response("OK", 200)

        except Exception as e:
            logging.info(f'Exception occurred: {e}')
            raise Exception(e)

        finally:
            if database_connection is not None:
                database_connection.close()

    def validate_jwt(self, jwt_payload):
        """Validate JWT, checking if the payload is present in the blacklist.

        Notes:
            The JWT Payload is present in the blacklist if
            the user has performed the logout. If I found it
            then the user is using a JWT no more valid.

        Returns:
            is_valid (boolean): flag to represent if jwt is either valid or not.

        Raises:
            JwtSessionExpired
        """
        database_connection = None
        is_valid = True

        try:
            db_user = self.local_secret_store[self._MAIN_DB_SECRET]["username"]
            db_password = self.local_secret_store[
                self._MAIN_DB_SECRET]["password"]
            database_connection = CloudSql().connect(
                self._CLOUD_SQL_INSTANCE_CONNECTION_NAME, db_user, db_password)
            with database_connection.cursor() as cursor:
                sql_statement = """
                    SELECT * FROM `edm-db-workflows`.backoffice_users_blacklist
                    WHERE jwt = %s
                    """
                cursor.execute(sql_statement, (jwt_payload, ))
                jwt = cursor.fetchone()
                if jwt is None:
                    return is_valid
                else:
                    raise JwtSessionExpired("session expired")

        except JwtSessionExpired as e:
            logging.info(f'Exception occurred: {e}')
            raise JwtSessionExpired(e)

        except Exception as e:
            logging.info(f'Exception occurred: {e}')
            raise Exception(e)

        finally:
            if database_connection is not None:
                database_connection.close()
