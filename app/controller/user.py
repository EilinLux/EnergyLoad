from services.cloudsql import CloudSql
from services.base64 import decode_base64

from flask import Response
import os
import logging
import json

# Load env variables
cloud_sql_instance_connection_name = os.environ.get("_CLOUD_SQL_INSTANCE_CONNECTION_NAME")
main_db_secret = os.environ.get("_MAIN_DB_SECRET")


class User:
    def __init__(self, local_secret_store, session_token):
        """Initialize class parameters"""
        self.local_secret_store = local_secret_store
        self.session_token = session_token

    def get(self):
        """Get user info."""
        database_connection = None

        try:

            # Get user id
            decoded = decode_base64(self.session_token)
            session = json.loads(decoded)
            user_id = session.get("user_id")

            # Get user info from database
            db_user = self.local_secret_store[main_db_secret]["username"]
            db_password = self.local_secret_store[main_db_secret]["password"]
            database_connection = CloudSql().raw_connect(
                cloud_sql_instance_connection_name, db_user, db_password)
            with database_connection.cursor() as cursor:
                sql_statement = """
                    SELECT username
                    FROM `edm-db-workflows`.backoffice_users
                    WHERE id = %s
                    """
                cursor.execute(sql_statement, (user_id, ))
                user = cursor.fetchone()

                # Manage the case the user is not in the database
                if user is None:
                    logging.info('User not found.')
                    return Response("bad request", 400)

                return Response(json.dumps(user),
                                200,
                                mimetype="application/json")

        except Exception as e:
            logging.error(f"Exception occurred: {e}.")
            return None

        finally:
            if database_connection is not None:
                database_connection.close()
