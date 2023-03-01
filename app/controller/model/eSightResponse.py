import jsonschema
from jsonschema import validate
import re
from datetime import datetime
from services.utils import _now
import pandas as pd
from services.monitoring import generate_uuid_from_string, update_receive_error_table, update_receive_table
from flask import Response
import logging
import json 
from controller.model.validate.receiveapi_schema import receive_api_jsonSchema
import traceback
from controller.model.config.send_errors import send_errors_config 
import os 

R_ERROR_DESTINATION_PATH = os.environ.get("_R_ERROR_DESTINATION_PATH")
ERROR_DESTINATION_BUCKET_NAME = os.environ.get("_ERROR_DESTINATION_BUCKET_NAME")
RESPONSE_ERROR_DESTINATION_BUCKET_NAME = os.environ.get(
    "_RESPONSE_ERROR_DESTINATION_BUCKET_NAME")



class eSightResponse():
    def __init__(self):
        # record starting process time
        self.starting = _now()
        # self.dashboard_output to monitor the dataflow
        self.dashboard_output = pd.DataFrame()

        self.errors_df = None
        self.ending = None

        self.data_feed_type = None
        self.local_market = None
        self.destination_path = None
        self.filename = None
        self.destination_bucket = None
        self.e_sight_Id = None
        self.messageId = None
        self.send_uuid = None
        self.e_sight_received_Json_tsIso8601 = None
        self.error_esightresponse = None
        self.uuid = None
        
    def validate_json(self, error_esightresponse):
        logging.info("Validating data from e-sight json error response...")
        try:
            validate(instance=error_esightresponse, schema=receive_api_jsonSchema)
            self.error_esightresponse = error_esightresponse
            logging.info("Validating _id...")            
            self.e_sight_Id = error_esightresponse["_id"]
            # generate a uuid for the process
            logging.info("Validating _id...")  
            self.uuid = generate_uuid_from_string(self.e_sight_Id,
                                                    self.starting)
            logging.info("Validating received_tsIso8601 in header...")  
            self.e_sight_received_Json_tsIso8601 = error_esightresponse[
                "header"]['received_tsIso8601']

            logging.info("Validating messageId in header...")  
            self.messageId = str(error_esightresponse["header"]['messageId'])
            self.send_uuid = error_esightresponse["header"]['messageId'].split(
                "_")[-1]
            self.data_feed_type = self._extract_data_feed_type()
            self.local_market = self._extract_local_market()

            return True
        except:
            return False


    def build_Json_filename(self):
        if self.e_sight_Id and self.messageId:
            return ("e-sightId__{}__messageId__{}.json".format(self.e_sight_Id, self.messageId)).replace("/", "_")
        else:
            return ("e-sight_message_received_at_{}".format(datetime.now()))

    def build_save_path(self):
        now = datetime.now()
        year, month, day = now.year, now.month, now.day
        if self.e_sight_Id and self.messageId:
            logging.info("building the file name")
            return "{}/{}/{}/{}/{}/{}/{}.json".format(R_ERROR_DESTINATION_PATH,
                                                self.data_feed_type, self.local_market,
                                                year, month, day, self.filename)
        else: 
            return "{}/{}/{}/{}.json".format(year, month, day, self.filename)

    def _handle_receving_error(self):
        logging.info("Extracting data from e-sight json error response...")

        self.errors_df = pd.DataFrame(self.error_esightresponse["errors"])

        self.ending = _now()
        self.errors_df["ending"] = self.ending
        self.errors_df["starting"] = self.starting
        self.errors_df = self.errors_df.rename(
            columns={
                "errorCode": "e_sight_response",
                "errorMessage": "e_sight_message"
            })
        self.errors_df["e_sight_response_type"] = "AsynchronousErrorResponse"
        self.errors_df["message_id"] = self.messageId
        self.errors_df["uuid"] = self.uuid
        self.errors_df["send_uuid"] = self.send_uuid
        self.errors_df[
            "e_sight_received_Json_tsIso8601"] = self.e_sight_received_Json_tsIso8601
        self.errors_df["e_sight_Id"] = self.e_sight_Id
        self.errors_df[
            "destination_bucket"] = RESPONSE_ERROR_DESTINATION_BUCKET_NAME
        self.errors_df["destination_path"] = self.destination_path

        receive_error_table_df = self.errors_df[[
            "uuid", "starting", "ending", "e_sight_Id",
            "e_sight_received_Json_tsIso8601", "send_uuid", "message_id",
            "e_sight_response_type", "e_sight_response", "e_sight_message",
            "datapointKey", "value", "tsIso8601", "destination_bucket",
            "destination_path"
        ]]

        update_receive_table(receive_error_table_df)

    def _handle_error(self, error_code):
        try:
            error_folder = send_errors_config[error_code]["name"]
            message = send_errors_config[error_code]["message"]
            error_type = error_folder
        except:
            error_type = traceback.format_exc()
            error_folder = "Error9999_Untracked"
            message = "Untracked Error"

        error_message = 'Error processing file received from e-sight. Cause: %s' % (
            traceback.format_exc())

        message = "{} \n More info: \n {} ".format(message, error_message)

        self.filename = self.build_Json_filename()
        self.destination_path = "{}/{}.json".format(error_folder, self.build_save_path())
        self.destination_bucket = ERROR_DESTINATION_BUCKET_NAME

        doc = {
            u'starting': self.starting,
            u'uuid': self.uuid,
            u'ending': _now(),
            u'error_code': error_code,
            u'error_type': error_type,
            u'error_message': message,
            u'destination_bucket': self.destination_bucket,
            u'destination_path': self.destination_path,
            u'original_bucket_name': "NA, error message from E-sight API",
            u'original_path': "NA, error message from E-sight API",
        }
        self.dashboard_output = self.dashboard_output.append(
            doc, ignore_index=True)
        update_receive_error_table(self.dashboard_output)
        logging.info(json.dumps(doc, indent=4))

        

    def _extract_data_feed_type(self):
        try:
            return re.search('^(\w+(-\w+)?)_(\w+)_', self.messageId)[1]
        except:
            return Response(
                "Malformed self.messageId, not able to retrieve data_feed_type", 400)


    def _extract_local_market(self):
        try:
            return re.search('^(\w+(-\w+)?)_(\w+)_', self.messageId)[3]
        except:
            return Response(
                "Malformed message_id, not able to retrieve local_market", 400)