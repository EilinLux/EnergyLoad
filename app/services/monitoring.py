from google.cloud import bigquery
import os
import uuid
import hashlib
from services.utils import _now
from services.cloudsql import CloudSql
from flask import jsonify

import logging
import os
import uuid

cloud_sql_instance_connection_name = os.environ.get(
    "_CLOUD_SQL_INSTANCE_CONNECTION_NAME")
main_db_secret = os.environ.get("_MAIN_DB_SECRET")

_PROJECT_ID = os.environ.get("_PROJECT_ID")
_TABLE_RECEIVE = os.environ.get("_TABLE_RECEIVE") 
_TABLE_RECEIVE_ERROR = os.environ.get("_TABLE_RECEIVE_ERROR")
_TABLE_SEND = os.environ.get("_TABLE_SEND") 
_TABLE_SEND_ERROR = os.environ.get("_TABLE_SEND_ERROR") 
_DATASET = os.environ.get("_DATASET")

def _database_connect(local_secret_store):
    """Connect to the database and return connection."""
    db_user = local_secret_store[main_db_secret]["username"]
    db_password = local_secret_store[main_db_secret]["password"]
    return CloudSql().raw_connect(cloud_sql_instance_connection_name, db_user,
                                  db_password)
                                  

class Event():
    def __init__(self, request, local_secret_store):
        self.starting = _now()
        self.ip = request.environ['REMOTE_ADDR']
                # 'REQUEST_URI = request.environ['REQUEST_URI'], 
        self.server_software = request.environ['SERVER_SOFTWARE']
        self.remote_port = request.environ['REMOTE_PORT']
        self.http_user_agent = request.environ['HTTP_USER_AGENT']
        self.request_method = request.environ['REQUEST_METHOD']
        self.path_info = request.environ['PATH_INFO']
        self.token = request.headers.get('X-Endpoint-Api-Userinfo')
        # name of the function
        self.endpoint  = request.endpoint
        self.body = "" #str(request.get_json())
        self.local_secret_store = local_secret_store


    def create_event(self, response):
        """Create an event."""
        database_connection = None
        self.status = response.status

        # Add a new record to the database
        database_connection = _database_connect(self.local_secret_store)
        with database_connection.cursor() as cursor:
                    #             CREATE TABLE logging_events (
                    # ip VARCHAR(500), server_software VARCHAR(500), remote_port VARCHAR(500), http_user_agent VARCHAR(500), 
                    # request_method VARCHAR(500), path_info VARCHAR(500), token VARCHAR(500), body VARCHAR(8000), endpoint VARCHAR(500), start_time VARCHAR(500), status VARCHAR(500));
                    
                sql_statement = """
                    INSERT INTO `edm-db-workflows`.`logging_events`
                        (ip , server_software , remote_port , http_user_agent , request_method , path_info , token, body,  endpoint , start_time, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """
                sql_values = (self.ip, self.server_software, self.remote_port, 
                self.http_user_agent, self.request_method, self.path_info, 
                self.token, self.body, self.endpoint, self.starting, self.status)
                cursor.execute(sql_statement, sql_values)
                logging.debug(f"Added an event.")
        database_connection.commit()
        return response





def generate_uuid_from_string(the_string, starting):
    """
    Returns String representation of the UUID of a hex md5 hash of the given string
    """
    # Instansiate new md5_hash
    md5_hash = hashlib.md5()

    the_string = starting + the_string
    # Pass the_string to the md5_hash as bytes
    md5_hash.update(the_string.encode("utf-8"))

    # Generate the hex md5 hash of all the read bytes
    the_md5_hex_str = md5_hash.hexdigest()

    # Return a String repersenation of the uuid of the md5 hash
    return str(uuid.UUID(the_md5_hex_str))


def update_receive_table(dashboard_output):
    print("Updating monitoring error dashboard for e-sight responses...")
    BQ = bigquery.Client()
    # create table
    table_id = "{}.{}.{}".format(_PROJECT_ID, _DATASET, _TABLE_RECEIVE)

    # insert into table
    job_config = bigquery.LoadJobConfig(
        autodetect=True,  # schema = schema_,
        write_disposition=bigquery.job.WriteDisposition.WRITE_APPEND)
    print("upload to tableid: {}".format(table_id))
    job = BQ.load_table_from_dataframe(
        dashboard_output, table_id,
        job_config=job_config)  # Make an API request.
    job.result()  # Wait for the job to complete.


def update_receive_error_table(dashboard_output):
    print("Updating monitoring error dashboard for e-sight responses...")
    BQ = bigquery.Client()
    # create table
    table_id = "{}.{}.{}".format(_PROJECT_ID, _DATASET, _TABLE_RECEIVE_ERROR)

    # insert into table
    job_config = bigquery.LoadJobConfig(
        autodetect=True,  # schema = schema_,
        write_disposition=bigquery.job.WriteDisposition.WRITE_APPEND)
    print("upload to tableid: {}".format(table_id))
    job = BQ.load_table_from_dataframe(
        dashboard_output, table_id,
        job_config=job_config)  # Make an API request.
    job.result()  # Wait for the job to complete.


def update_send_error_table(dashboard_output):
    print("Updating monitoring error dashboard for the general pipeline...")
    BQ = bigquery.Client()
    # create table
    table_id = "{}.{}.{}".format(_PROJECT_ID, _DATASET, _TABLE_SEND_ERROR)

    # insert into table
    job_config = bigquery.LoadJobConfig(
        autodetect=True,  # schema = schema_,
        write_disposition=bigquery.job.WriteDisposition.WRITE_APPEND)
    print("upload to tableid: {}".format(table_id))
    job = BQ.load_table_from_dataframe(
        dashboard_output, table_id,
        job_config=job_config)  # Make an API request.
    job.result()  # Wait for the job to complete.


def update_send_table(dashboard_output):
    print("Updating monitoring sending dashboard...")
    dashboard_output = dashboard_output[[
        "uuid", "starting", "ending", "e_sight_message", "e_sight_response",
        "e_sight_response_type", "message_id", "data_feed_type",
        "local_market", "site_id", "meter_id", "original_bucket",
        "original_path", "destination_bucket", "destination_path",
        "dataimportcode", "datapointKey", "tsIso8601", "value"
    ]]
    BQ = bigquery.Client()
    # create table
    table_id = "{}.{}.{}".format(_PROJECT_ID, _DATASET, _TABLE_SEND)

    # _schema = BQ.schema_from_json(SEND_SCHEMA)

    # insert into table
    job_config = bigquery.LoadJobConfig(
        autodetect=True,  # schema=_schema,  #
        write_disposition=bigquery.job.WriteDisposition.WRITE_APPEND)
    print("upload to tableid: {}".format(table_id))
    job = BQ.load_table_from_dataframe(
        dashboard_output, table_id,
        job_config=job_config)  # Make an API request.
    job.result()  # Wait for the job to complete.
