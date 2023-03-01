# management.py
# Python Module used to allow administration to create,
# modify and manage the lifecycle of users accounts.
from services.cloudsql import CloudSql
from controller import commons, validator

from flask import Response
from argon2 import PasswordHasher
import json
import logging
import os
import uuid

cloud_sql_instance_connection_name = os.environ.get(
    "_CLOUD_SQL_INSTANCE_CONNECTION_NAME")
main_db_secret = os.environ.get("_MAIN_DB_SECRET")


def create(session_token, type, user, local_secret_store):
    """Create a user.
    the API call should contain: username, password, type"""
    database_connection = None

    try:

        # Generate Uuid v4
        user['id'] = str(uuid.uuid4())

        # Hash the password
        user['password'] = PasswordHasher().hash(user.get('password'))

        # Add a new record to the database
        database_connection = _database_connect(local_secret_store)
        with database_connection.cursor() as cursor:

            # Search for the user into user table 
            sql_statement = f"""
                SELECT id, username
                FROM `edm-db-workflows`.`backoffice_users`
                WHERE username = %s
                """
            sql_values = (user.get('username'), )
            cursor.execute(sql_statement, sql_values)
            row = cursor.fetchone()
            logging.debug(row)

            # If the user does not exists
            if row is None or row['username'] is None:
                logging.debug("User not found.")

                # Add user account into backoffice_users
                user['account_id'] = str(uuid.uuid4())
                sql_statement = """
                    INSERT INTO `edm-db-workflows`.`backoffice_users`
                        (id, username, password, type, creator)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                sql_values = (user.get('id'), user.get('username'),
                              user.get('password'), type, session_token)
                cursor.execute(sql_statement, sql_values)
                logging.debug(f"Added user account.")
                user_id = user.get('id')

                database_connection.commit()
                return Response(json.dumps({"id": user_id}),
                                201,
                                mimetype="application/json")

            else:
                logging.debug("User already exists.")

                user_id = row.get('id')

                database_connection.commit()
                return Response("User already exists with id: {}. Use  methods as 'PATCH' with the /api/v1/management/users/user/edit/<id>' API if you want to edit the user".format(user_id),
                                200)

    except Exception as e:
        logging.error(f"Exception occurred: {e}.")
        raise Exception(e)

    finally:
        if database_connection is not None:
            database_connection.close()


def modify(type, user_id, data, local_secret_store):
    """"Modify a user object."""
    database_connection = None

    try:

        # Validate
        validated = validator.validate_mngmnt_users_modify(data)
        if len(validated) == 0:
            return Response("bad request", 400)

        # In case there is password, hash it
        password_key = 'password'
        if password_key in validated.keys():
            data[password_key] = PasswordHasher().hash(data[password_key])

        # Add a new record to the database
        database_connection = _database_connect(local_secret_store)
        with database_connection.cursor() as cursor:
            separator = ", "
            sql_statement = f"""
                UPDATE `edm-db-workflows`.`backoffice_users`
                    SET {separator.join([key+'=%s' for key in validated])}
                    WHERE id=%s
                """
            sql_values = tuple(data[key] for key in validated) + (user_id, )
            logging.debug(f"SQL STATEMENT: {sql_statement}.")
            logging.debug(f"SQL VALUES: {sql_values}.")
            cursor.execute(sql_statement, sql_values)
            database_connection.commit()
            return Response("updated", 200)

    except Exception as e:
        logging.error(f"Exception occurred: {e}.")
        raise Exception(e)

    finally:
        if database_connection is not None:
            database_connection.close()


def deactivate(user_id, local_secret_store):
    """deactivated a user."""
    database_connection = None
    try:
        # Add a new record to the database
        database_connection = _database_connect(local_secret_store)
        with database_connection.cursor() as cursor:


            # Remove user account
            sql_statement = f"""
                UPDATE `edm-db-workflows`.`backoffice_users`
                    SET status = "deactivated"
                    WHERE id=%s
                """
            sql_values = (user_id, )
            cursor.execute(sql_statement, sql_values)
            logging.debug(f"Removed user account.")

            database_connection.commit()
            return Response("deactivated", 200)

    except Exception as e:
        logging.error(f"Exception occurred: {e}.")
        raise Exception(e)

    finally:
        if database_connection is not None:
            database_connection.close()


def _database_connect(local_secret_store):
    """Connect to the database and return connection."""
    db_user = local_secret_store[main_db_secret]["username"]
    db_password = local_secret_store[main_db_secret]["password"]
    return CloudSql().raw_connect(cloud_sql_instance_connection_name, db_user,
                                  db_password)
