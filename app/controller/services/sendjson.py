from services.cloudstorage import collect_files_from_bucket
from services.esight import get_access_token, list_siteid, list_meterid, send_to_e_sight_dev, SendingToESightException, SiteIdListException, AccessTokenException, MeterIdListException
from controller.model.JsonSendFile import JsonSendFile, DownloadJsonException, NoSiteID, NoMeterID
import logging
from flask import Response
from services.monitoring import update_send_table, update_send_error_table
import os
from services.cloudstorage import move_blob



_SOURCE_BUCKET_NAME = os.environ.get("_SOURCE_BUCKET_NAME") 
Username = os.environ.get("_USERNAME")
Password = os.environ.get("_PASSWORD")
main_db_secret = os.environ.get("_MAIN_DB_SECRET")
post_Password = os.environ.get("_POST_PASSWORD")
post_Username = os.environ.get("_POST_USER")

class SendJsons:
    def __init__(self, local_secret_store, session_token):
        """Initialize class parameters"""
        self.local_secret_store = local_secret_store
        self.session_token = session_token

    def send_files_to_e_sight(self, file_name=None):
        try:

            files_list = collect_files_from_bucket(_SOURCE_BUCKET_NAME, prefix=file_name)

            if (files_list):

                # # authentication
                # or use for now get_access_token(Username, Password)
                access_token = get_access_token(
                    Username, Password)

                # collect updated lists for siteid and meterid
                site_ids_list = list_siteid(access_token)
                meter_id_list = list_meterid(access_token)

                # for each file in the processed bucket
                for original_path in files_list:
                    self.send_json(original_path, site_ids_list, meter_id_list)

                return Response(
                    "Success: {} file(s) have been processed".format((len(files_list))), 201)

            else:
                return Response(
                    "Empty bucket! Nothing to send to e-sight", 200)  

        except AccessTokenException as e:
            logging.error(f"Exception occurred while performing get_access_token function: {e}.")
            return Response(
                    "Error while contacting e-sight for JWT token", 400)           
        
        except SiteIdListException as e:
            logging.error(f"Exception occurred while performing list_siteid function: {e}.")
            return Response(
                    "Error while contactin e-sight for site id list", 400)   
        
        except MeterIdListException as e:
            logging.error(f"Exception occurred while performing list_meterid function: {e}.")
            return Response(
                    "Error while contacting e-sight for meter id list", 400)  
        


        except Exception as e:
            logging.error(f"Exception occurred: {e}.")
            return Response(
                    f"Exception occurred: {e}.", 500)  

    def send_json(self, original_path, site_ids_list, meter_id_list):
        logging.info("Processing file: {}".format(original_path))
        e_sight_json = JsonSendFile(original_path, _SOURCE_BUCKET_NAME)
        e_sight_json.download_file()

        if not (e_sight_json.e_sight_response):
            e_sight_json.validate_extract_info_from_json()

        if not (e_sight_json.e_sight_response):
            logging.info("Checking meter and site ids...")
            e_sight_json.check_meter_id(meter_id_list)

        if not (e_sight_json.e_sight_response):
            logging.info("Checking meter and site ids...")
            e_sight_json.check_site_id(site_ids_list)

        if not (e_sight_json.e_sight_response):
            logging.info("Sending to e-sight...")
            e_sight_json.e_sight_response = send_to_e_sight_dev(
                e_sight_json.file_json, post_Username, post_Password)
            

        e_sight_json._handle_status()

        update_send_table(e_sight_json.dashboard_output)

        if e_sight_json.e_sight_response != 200:

            update_send_error_table(
                e_sight_json.error_dashboard_output)

        move_blob(e_sight_json.original_bucket, e_sight_json.original_path, e_sight_json.destination_bucket, e_sight_json.destination_path)
        
        logging.info(f"Finished with {e_sight_json.original_path}")
    
