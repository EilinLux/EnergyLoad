from flask import request, Response
from controller.model.eSightResponse import eSightResponse
from services.cloudstorage import store_json_locally, upload2storage_json_error
import traceback


class ReceiveErrorJson():
    def __init__(self, local_secret_store, session_token):
        """Initialize class parameters"""
        self.local_secret_store = local_secret_store
        self.session_token = session_token

    def receive_error_json_from_e_sight(self):

        json_data = request.get_json()

        e_sight_response = eSightResponse()

        #  validate input
        if json_data == None:
            error_code = "EmptyJson"
            e_sight_response._handle_error(error_code)  
            return Response(error_code, 400)


        elif e_sight_response.validate_json(json_data)==False: 
            error_code = "InvalidJsonReceived"
            e_sight_response._handle_error(error_code)
            
            # store Json response to a new bucket
            store_json_locally(e_sight_response.filename, json_data)
            upload2storage_json_error(e_sight_response.filename,
                                        e_sight_response.destination_path)
            return Response(error_code, 400)

        else:
            try:

                e_sight_response.destination_path = e_sight_response.build_save_path()
                e_sight_response.filename = e_sight_response.build_Json_filename()

                # upload monitoring dashboard
                e_sight_response._handle_receving_error()
                # store Json response to a new bucket
                store_json_locally(e_sight_response.filename, json_data)
                upload2storage_json_error(e_sight_response.filename,
                                          e_sight_response.destination_path)
                return Response(
                    "<h1>Success on processing a file</h1><p>Processed error file with</p><p>e-sight id: {}</p><p>message_id: {}</p>"
                    .format(e_sight_response.e_sight_Id,
                            e_sight_response.messageId), 201)
            except:
                error_code = "Generic"
                e_sight_response._handle_error(error_code)
                # store Json response to a new bucket
                store_json_locally(e_sight_response.filename, json_data)
                upload2storage_json_error(e_sight_response.filename,
                                          e_sight_response.destination_path)
                return Response(
                    "<h1>Error on processing a file</h1><p>error file with</p><p> e-sight id: {}</p><p>message_id: {}</p><p>{}</p>"
                    .format(e_sight_response.e_sight_Id,
                            e_sight_response.messageId,
                            traceback.format_exc()), 500)