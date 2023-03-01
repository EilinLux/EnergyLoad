from services.utils import _now
from services.uuid import generate_uuid_from_string
import pandas as pd
from google.cloud import storage
from controller.model.validate.sendapi_schema import send_api_jsonSchema
from services.esight import send_to_e_sight_dev
from controller.model.config.send_errors import send_errors_config

import json
import jsonschema
from jsonschema import validate
import re
import traceback
from flask import Response
import logging
import os 


class DownloadJsonException(Exception):
    """Exception for the e-sight session."""

    def __init__(self, message):
        super().__init__(message)

class NoSiteID(Exception):
    """Exception for the e-sight session."""

    def __init__(self, message):
        super().__init__(message)

class NoMeterID(Exception):
    """Exception for the e-sight session."""

    def __init__(self, message):
        super().__init__(message)

class InvalidJson(Exception):
    """Exception for the e-sight session."""

    def __init__(self, message):
        super().__init__(message)

_ERROR_DESTINATION_BUCKET_NAME = os.environ.get("_ERROR_DESTINATION_BUCKET_NAME") 
_SUCCESS_DESTINATION_BUCKET_NAME = os.environ.get("_SUCCESS_DESTINATION_BUCKET_NAME")

post_Password = os.environ.get("_POST_PASSWORD")
post_Username = os.environ.get("_POST_USER")

_S_ERROR_DESTINATION_PATH = os.environ.get("_S_ERROR_DESTINATION_PATH")


class JsonSendFile():
    def __init__(self, original_path, SOURCE_BUCKET_NAME):
        # record starting process time
        self.starting = _now()

        # retrieve from CloudStorage
        self.original_path = original_path
        self.original_bucket = SOURCE_BUCKET_NAME

        # generate a uuid for the process
        self.uuid = generate_uuid_from_string(self.original_path,
                                              self.starting)

        # self.dashboard_output to monitor the dataflow
        self.dashboard_output = pd.DataFrame()
        self.error_dashboard_output = pd.DataFrame()

        self.file_json = None
        self.gatewayTypeUrn = None
        self.gatewayUrn = None
        self.messageId = None
        self.datapointValues = None
        self.local_market = None
        self.data_feed_type = None
        self.meter_id = None
        self.site_id = None

        self.datapointKey = None
        self.dataimportcode = None
        self.destination_path = None
        self.destination_bucket = None
        self.e_sight_response = None

    def download_file(self):
        try:
            logging.info("Downloading file {}".format(self.original_path))
            storageclient = storage.Client()
            #  Retrieves a bucket by name, bucket_name (string) – The name of the bucket
            bucket = storageclient.get_bucket(self.original_bucket)
            # The name of the blob. This corresponds to the unique path of the object in the bucket.
            self.blob = bucket.blob(self.original_path)
            self.file_json = json.loads(self.blob.download_as_string(client=None))
        except:
            error_code = "DownloadJsonException"
            message = "Error downloading file {}".format(self.original_path)
            self.process_warning(error_code, message)


    def validate_extract_info_from_json(self):
    
        logging.info("Extracting info from JSON...")
        # self.gatewayTypeUrn = self.file_json["header"]['gatewayTypeUrn']
        try: 
            self.gatewayTypeUrn = self.file_json["header"]['gatewayTypeUrn']
        except: 
            error_code = "NoGatewayTypeUrn"
            message = "gatewayTypeUrn in file {}".format(self.original_path)
            self.process_warning(error_code, message)

        # self.gatewayUrn = self.file_json["header"]['gatewayUrn']
        try: 
            self.gatewayUrn = self.file_json["header"]['gatewayUrn']
        except: 
            error_code = "NoGatewayUrn"
            message = "gatewayUrn in file {}".format(self.original_path)
            self.process_warning(error_code, message)

        # self.messageId = "{}_{}".format(
        #     self.file_json["header"]['messageId'], self.uuid)
        try: 
            self.messageId = "{}_{}".format(
            self.file_json["header"]['messageId'], self.uuid)
        except: 
            error_code = "NoMessageId"
            message = "messageId in file {}".format(self.original_path)
            self.process_warning(error_code, message)


        try: 
            self.datapointValues = self.file_json["gatewayData"]['datapointValues']
        except: 
            error_code = "NoDatapointValues"
            message = "datapointValues in file {}".format(self.original_path)
            self.process_warning(error_code, message)

        try: 
            self.local_market = re.search(
            'urn:esight:assets:edm:(\w+):(\w+(-\w+)?)',
            self.gatewayTypeUrn)[1]
        except: 
            error_code = "NoLocalMarket"
            message = "LocalMarket in file {}".format(self.original_path)
            self.process_warning(error_code, message)


        try: 
            self.data_feed_type = re.search(
            'urn:esight:assets:edm:(\w+):(\w+(-\w+)?)',
            self.gatewayTypeUrn)[2]
        except: 
            error_code = "NoDataFeedType"
            message = "DataFeedType in file {}".format(self.original_path)
            self.process_warning(error_code, message)

        # self.meter_id =  re.search('.+:([^;]*)$', self.gatewayUrn)[1]
        try: 
            self.meter_id = re.search('.+:([^;]*)$', self.gatewayUrn)[1]

        except: 
            error_code = "NoMeterIDInJson"
            message = "No MeterID in Json sent to e-sight in file {}".format(self.original_path)
            self.process_warning(error_code, message)

        # self.site_id = re.search('.+:([^;]*):([^;]*)$', self.gatewayUrn)[1]
        try: 
            self.site_id = re.search('.+:([^;]*):([^;]*)$', self.gatewayUrn)[1]

        except: 
            error_code = "NoSiteIDInJson"
            message = "No SiteID in Json sent to e-sight in file {}".format(self.original_path)
            self.process_warning(error_code, message)



    def check_meter_id(self, meter_id_list):
        """"
        Meter id list returns something like this, but hte example given is different 
        ['LU_VPC_Temp_28', 'LU_VPC_Temp_27', 'LU_VPC_Temp_26', 'LU_VPC_Temp_39',
         'LU_VPC_Temp_31', 'LU_VPC_Temp_29', 'LU_VPC_Temp_30', 'LU_VPC_Temp_32', 'LU_VPC_Temp_33', 'LU_VPC_Temp_34', 'LU_VPC_Temp_35', 'LU_VPC_Temp_38', 'LU_VPC_Elec_4', 'LU_VPC_Temp_37', 'LU_VPC_Temp_36', 'LU_VPC_Temp_25', 'LU_VPC_Elec_3', 'LU_VPC_Temp_40', 'LU_VPC_Elec_2', 'LU_VPC_Temp_41', 'LU_VPC_Temp_43', 'LU_VPC_Temp_44', 'LU_VPC_Temp_45', 'LU_VPC_Temp_47', 'LU_VPC_Temp_48', 'LU_VPC_Temp_46', 'LU_VPC_Temp_49', 'LU_VPC_Temp_60', 'LU_VPC_Temp_42', 'LU_VPC_Temp_50', 'LU_VPC_Temp_51', 'LU_VPC_Temp_52', 'LU_VPC_Temp_53', 'LU_VPC_Temp_54', 'LU_VPC_Temp_56', 'LU_VPC_Temp_58', 'LU_VPC_Temp_57', 'LU_VPC_Temp_55', 'LU_VPC_Temp_59', 'LU_VPC_Elec_11', 'LU_VPC_Elec_5', 'LU_VPC_Elec_1', 'LU_VPC_Elec_10', 'LU_VPC_Temp_1', 'LU_VPC_Temp_2', 'LU_VPC_Temp_3', 'LU_VPC_Temp_4', 'LU_VPC_Temp_6', 'LU_VPC_Temp_10', 'LU_VPC_Temp_7', 'LU_VPC_Temp_8', 'LU_VPC_Temp_9', 'LU_VPC_Temp_11', 'LU_VPC_Temp_5', 'LU_VPC_Temp_12', 'LU_VPC_Temp_13', 'LU_VPC_Temp_14', 'LU_VPC_Temp_15', 'LU_VPC_Temp_16', 'LU_VPC_Temp_17', 'LU_VPC_Temp_19', 'LU_VPC_Temp_18', 'LU_VPC_Temp_22', 'LU_VPC_Temp_21', 'LU_VPC_Temp_23', 'LU_VPC_Temp_20', 'LU_VPC_Temp_24', 'LU_VPC_Elec_6', 'LU_VPC_Elec_7', 'LU_VPC_Elec_8', 'LU_VPC_Elec_9', 'LU_VPC_Temp_61', 'LU_VPC_Temp_62', 'HU_1001_Elec_2', 'HU_1001_Elec_1', 'HU_1002_Elec_2', 'HU_1003_Elec_1', 'HU_1002_Elec_1', 'HU_1003_Elec_2', 'HU_1005_Elec_1', 'HU_1004_Elec_1', 'HU_1009_Elec_1', 'HU_1007_Elec_1', 'HU_1009_Elec_2', 'HU_1010_Elec_1', 'HU_1012_Elec_1', 'HU_1011_Elec_1', 'HU_1011_Elec_2', 'HU_1013_Elec_1', 'HU_1014_Elec_1', 'HU_1012_Elec_2', 'HU_1013_Elec_2', 'HU_1015_Elec_1', 'HU_1016_Elec_1', 'HU_1017_Elec_1', 'HU_1017_Elec_2', 'HU_1016_Elec_2', 'HU_1019_Elec_1', 'HU_1020_Elec_1', 'HU_1019_Elec_2', 'HU_1021_Elec_1', 'HU_1022_Elec_1', 'HU_1022_Elec_2', 'HU_1021_Elec_2', 'HU_1024_Elec_1', 'HU_1024_Elec_2', 'HU_1026_Elec_1', 'HU_1028_Elec_1', 
        'HU_1029_Elec_3', 'HU_1029_Elec_2', 'HU_1031_Elec_1', 'HU_1032_Elec_1', 'HU_1034_Elec_1', 'HU_1032_Elec_2', 'HU_1035_Elec_1', 'HU_1037_Elec_2', 'HU_1037_Elec_1', 'HU_1039_Elec_1', 'HU_1039_Elec_2', 'HU_1040_Elec_1', 'HU_1040_Elec_2', 'HU_1043_Elec_1', 'HU_1045_Elec_1', 'HU_1044_Elec_1', 'HU_1045_Elec_2', 'HU_1047_Elec_1', 'HU_1047_Elec_2', 'HU_1049_Elec_2', 'HU_1048_Elec_2', 'HU_1048_Elec_1', 'HU_1049_Elec_1', 'HU_1051_Elec_1', 'HU_1052_Elec_1', 'HU_1054_Elec_1', 'HU_1053_Elec_1', 'HU_1052_Elec_2', 'HU_1056_Elec_1', 'HU_1057_Elec_1', 'HU_1058_Elec_1', 'HU_1057_Elec_2', 'HU_1058_Elec_2', 'HU_1059_Elec_1', 'HU_1061_Elec_1', 'HU_1060_Elec_1', 'HU_1059_Elec_2', 'HU_1060_Elec_2', 'HU_1061_Elec_2', 'HU_3956_Elec_1', 'HU_1063_Elec_1', 'HU_3957_Elec_1', 'HU_1063_Elec_2', 'HU_3962_Elec_1', 'HU_3958_Elec_1', 'HU_3963_Elec_1', 'HU_3960_Elec_1', 'HU_3965_Elec_1', 'HU_3978_Elec_
        
        """
        logging.info("Checking if {} in meterid list...".format(self.meter_id))
        logging.info("meterid list...".format(meter_id_list))

        if not self.meter_id in meter_id_list:
            error_code = "NoMeterId"
            message = f"Meter id {self.meter_id} not found in e-sight list"
            self.process_warning(error_code, message)

    def check_site_id(self, site_ids_list):

        code_site_id = self.local_market.upper() + "_" + self.site_id
        logging.info("Checking if {} in siteid list...".format(code_site_id))

        if not code_site_id in site_ids_list:
            error_code = "NoSiteId"
            message = f"Site id {self.code_site_id} not found in e-sight list"
            self.process_warning(error_code, message)


    def process_warning(self, error_code, message=None):
        self._handle_error(error_code,  message)
        self.e_sight_response = error_code
        logging.info("======================{}======================".format(
            self.e_sight_response))
        


    def _handle_status(self):

        e_sight_response = self.e_sight_response

        logging.info("Uploading info on the process...")
        
        message = send_errors_config[str(e_sight_response)]["message"]
        response_type = send_errors_config[str(e_sight_response)]["name"]
        # ====================
        # SUCCESS: 200
        # ====================

        if e_sight_response == 200:
            self.destination_path = self.original_path
            self.destination_bucket = _SUCCESS_DESTINATION_BUCKET_NAME

            for each_consumption in range(len(self.datapointValues)-1):

                doc = {
                    # info on the process
                    u'uuid':
                    self.uuid,
                    u'starting':
                    self.starting,
                    u'ending':
                    _now(),
                    u'e_sight_response':
                    str(e_sight_response),
                    u'e_sight_response_type':
                    response_type,
                    u'e_sight_message':
                    message,

                    # info on storage
                    u'destination_bucket':
                    self.destination_bucket,
                    u'destination_path':
                    self.destination_path,
                    u'original_bucket':
                    self.original_bucket,
                    u'original_path':
                    self.original_path,

                    # info on consumption
                    u'message_id':
                    self.messageId,
                    u'data_feed_type':
                    self.data_feed_type,
                    u'local_market':
                    self.local_market,
                    u'site_id':
                    self.site_id,
                    u'meter_id':
                    self.meter_id,
                    u'datapointKey':
                    self.datapointValues[each_consumption]['datapointKey'],
                    u'value':
                    self.datapointValues[each_consumption]['value'],
                    u'tsIso8601':
                    self.datapointValues[each_consumption]['tsIso8601'],
                    u'dataimportcode':
                    "{}|{}|{}".format(
                        self.gatewayTypeUrn, self.gatewayUrn,
                        self.datapointValues[each_consumption]['datapointKey'])
                }

                self.dashboard_output = self.dashboard_output.append(
                    doc, ignore_index=True)

        # ====================
        # UNSUCCESS: all the rest
        # ====================
        else:
            if not self.destination_path:
                message = 'Error processing file \'%s\'. Cause: %s' % (
                    self.original_path, traceback.format_exc())
                self.destination_path = "{}/{}/{}".format(_S_ERROR_DESTINATION_PATH,
                                                        str(e_sight_response),
                                                        self.original_path)
                self.destination_bucket = _ERROR_DESTINATION_BUCKET_NAME

            doc = {
                # info on the process
                u'uuid': self.uuid,
                u'starting': self.starting,
                u'ending': _now(),
                u'e_sight_response': str(e_sight_response),
                u'e_sight_response_type': response_type,
                u'e_sight_message': message,

                # info on storage
                u'destination_bucket': self.destination_bucket,
                u'destination_path': self.destination_path,
                u'original_bucket': self.original_bucket,
                u'original_path': self.original_path,

                # info on consumption
                u'message_id': self.messageId,
                u'data_feed_type': self.data_feed_type,
                u'local_market': self.local_market,
                u'site_id': self.site_id,
                u'meter_id': self.meter_id,
                u'datapointKey': None,
                u'value': None,
                u'tsIso8601': None,
                u'dataimportcode': None
            }

            self.dashboard_output = self.dashboard_output.append(
                doc, ignore_index=True)

    def _handle_error(self, error_code, message):

        if message:
            error_type = error_code
            pass
        else:
            try:
                error_type = send_errors_config[error_code]["name"]
                message = send_errors_config[error_code]["message"]
            except:
                error_type =  "UntrackedError"
                message =  traceback.format_exc()

        message = 'Error processing file \'%s\'. Cause: %s' % (
            self.original_path, message)

        self.destination_path = "{}/{}/{}".format(_S_ERROR_DESTINATION_PATH,
                                                error_type,
                                                self.original_path)
        self.destination_bucket = _ERROR_DESTINATION_BUCKET_NAME

        doc = {
            u'starting': self.starting,
            u'uuid': self.uuid,
            u'ending': _now(),
            u'error_code': error_code,
            u'error_type': error_type,
            u'error_message': message,
            u'destination_bucket': self.destination_bucket,
            u'destination_path': self.destination_path,
            u'original_bucket_name': self.original_bucket,
            u'original_path': self.original_path,
        }
        self.error_dashboard_output = self.error_dashboard_output.append(
            doc, ignore_index=True)
        logging.info(json.dumps(doc, indent=4))
