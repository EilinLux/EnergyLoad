from google.cloud import secretmanager_v1beta1 as secretmanager
import time
import json
import google.auth.jwt
import google.auth.crypt
from services.monitoring import _database_connect
import logging


class JwtSessionExpired(Exception):
    """Exception for the JWT session."""

    def __init__(self, message):
        super().__init__(message)


class RegisterJWT:
    def __init__(self, local_secret_store, user_id, jwt, starting, expiring,  payload):
        """Create an log for a JWT."""
        database_connection = None

        # Add a new record to the database
        database_connection = _database_connect(local_secret_store)
        with database_connection.cursor() as cursor:
                sql_statement = """
                    INSERT INTO `edm-db-workflows`.`jwt`
                        (user_id, jwt, start_validity, expiring,  payload)
                    VALUES (%s, %s, %s, %s, %s)
                    """

                logging.debug(f"Added jwt.")
        database_connection.commit()


class Jwt:
    def __init__(self, _LOCAL_SECRET_STORE, _PROJECT_ID, _SERVICE_ACCOUNT_JWT_SECRET, _ESP_URL):
        self._PROJECT_ID = _PROJECT_ID
        self._SERVICE_ACCOUNT_JWT_SECRET = _SERVICE_ACCOUNT_JWT_SECRET
        self._ESP_URL = _ESP_URL
        self._LOCAL_SECRET_STORE = _LOCAL_SECRET_STORE

    def load(self, secret_id):
        """Load secret variables from GCP Secret Manager"""
        secret_manager_client = secretmanager.SecretManagerServiceClient()
        secret_path = secret_manager_client.secret_version_path(
            self._PROJECT_ID, secret_id, "latest")
        downloaded_secret = secret_manager_client.access_secret_version(
            secret_path)
        return downloaded_secret.payload.data.decode("UTF-8")

    def generate(self, data, expiry_length=3600 * 24): #TODO change to only 3600 
        """Generate JWT."""

        sa_keyfile = json.loads(self.load(self._SERVICE_ACCOUNT_JWT_SECRET))
        sa_email = sa_keyfile["client_email"]
        audience = self._ESP_URL
        now = int(time.time())
        expiring = now + expiry_length
        # build payload
        payload = {
            'iat': now,
            # expires after 'expiry_length' seconds.
            "exp": expiring ,
            # iss must match 'issuer' in the security configuration in your
            # swagger spec (e.g. service account email). It can be any string.
            'iss': sa_email,
            # aud must be either your Endpoints service name, or match the value
            # specified as the 'x-google-audience' in the OpenAPI document.
            'aud': audience,
            # sub and email should match the service account's email address
            'sub': sa_email,
            'email': sa_email,
            'user_id': data.get('user_id'),
            # 'allowed_for': data.get('allowed_for') # admin[all], e_sight[/api/v1/service/receive/errorjson,logout ], individual [user, logout]
        }

        signer = google.auth.crypt.RSASigner.from_service_account_info(
            sa_keyfile)
        jwt = google.auth.jwt.encode(signer, payload)
        
        # # TODO login table
        RegisterJWT(self._LOCAL_SECRET_STORE, data.get('user_id'), jwt, now, expiring, payload)


        return jwt
