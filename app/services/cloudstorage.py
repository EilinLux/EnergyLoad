from google.cloud import storage
from google.cloud.storage.blob import Blob
from services import secretmanager
from services import utils
import datetime
import os
import logging
import json



R_ERROR_DESTINATION_PATH = os.environ.get("_R_ERROR_DESTINATION_PATH")
ERROR_DESTINATION_BUCKET_NAME = os.environ.get("_ERROR_DESTINATION_BUCKET_NAME")
RESPONSE_ERROR_DESTINATION_BUCKET_NAME = os.environ.get(
    "_RESPONSE_ERROR_DESTINATION_BUCKET_NAME")


def download_blob(object_uri):
    """Download a blob from the bucket."""
    s = object_uri.split("/")
    bucket_name, destination_blob_name = s[2], "/".join(s[3:])
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    return blob.download_as_string()


def upload_blob(object_uri, source_str, content_type="text/plain"):
    """Upload a blob to the bucket."""
    storage_client = storage.Client()
    blob = Blob.from_string(object_uri)
    blob.upload_from_string(data=source_str,
                            content_type=content_type,
                            client=storage_client)


def delete_blob(object_uri):
    """Delete a blob from the bucket"""
    s = object_uri.split("/")
    bucket_name, blob_name = s[2], "/".join(s[3:])
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()


def copy_blob(bucket_name, blob_name, destination_bucket_name,
              destination_blob_name):
    """Copies a blob from one bucket to another with a new name."""
    # bucket_name = "your-bucket-name"
    # blob_name = "your-object-name"
    # destination_bucket_name = "destination-bucket-name"
    # destination_blob_name = "destination-object-name"

    storage_client = storage.Client()

    source_bucket = storage_client.bucket(bucket_name)
    source_blob = source_bucket.blob(blob_name)
    destination_bucket = storage_client.bucket(destination_bucket_name)

    blob_copy = source_bucket.copy_blob(source_blob, destination_bucket,
                                        destination_blob_name)

    logging.debug(
        "Blob {} in bucket {} copied to blob {} in bucket {}.".format(
            source_blob.name,
            source_bucket.name,
            blob_copy.name,
            destination_bucket.name,
        ))


def get_upload_signed_url(object_uri, exp=5, method='PUT', version="v4"):
    """Get a signed URL for uploading purposes."""
    storage_client = storage.Client()
    blob = Blob.from_string(object_uri)
    return blob.generate_signed_url(expiration=datetime.timedelta(minutes=exp),
                                    method=method,
                                    version=version,
                                    client=storage_client)


def generate_upload_signed_url_v4(object_uri,
                                  mime_type,
                                  exp_minutes=1,
                                  method='PUT',
                                  version="v4"):
    """Get a signed URL for uploading purposes."""
    s = object_uri.split("/")
    bucket_name, destination_blob_name = s[2], "/".join(s[3:])

    # Check if service account file is not present
    service_account_file = "service_account.json"
    if not os.path.isfile(service_account_file):
        # Get service account from Secret Manager
        service_account = secretmanager.download_single(
            os.environ.get("_PROJECT_ID"),
            "service-account",
            "latest",
            'UTF-8')

        # Create and set service account file
        f = open(service_account_file, "w")
        f.write(service_account)
        f.close()

    # Create Signed URL
    signer_storage_client = storage.Client.from_service_account_json(
        service_account_file)
    bucket = signer_storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    return blob.generate_signed_url(
        version=version,
        expiration=datetime.timedelta(minutes=exp_minutes),
        method=method,
        content_type=mime_type)


def duplicate_gcs_file(bucket_name, workflow_id, workflow_version,
                       source_instance_id, destination_instance_id):
    # TODO per migliorare le prestazioni fare una copia diretta su GCS

    folder_name = workflow_id
    file_name_source = f"{workflow_id}_v{workflow_version}_{source_instance_id}.json"
    gcs_uri_source = f'gs://{bucket_name}/{folder_name}/{file_name_source}'
    logging.debug(f"Download following resource: {gcs_uri_source}.")
    input_data = download_blob(gcs_uri_source)

    file_name_destination = f"{workflow_id}_v{workflow_version}_{destination_instance_id}.json"
    gcs_uri_destination = f'gs://{bucket_name}/{folder_name}/{file_name_destination}'
    logging.debug(
        f"Trying to upload the following resource: {gcs_uri_destination}.")
    upload_blob(gcs_uri_destination,
                input_data,
                content_type="application/json")
    return gcs_uri_destination


def duplicate_context_file(bucket_name, workflow_id, workflow_version,
                           source_instance_id, destination_instance_id):

    folder_name = workflow_id
    file_name_source = f"{workflow_id}_v{workflow_version}_{source_instance_id}.json"
    gcs_uri_source = f'gs://{bucket_name}/{folder_name}/{file_name_source}'
    logging.debug(f"Download following resource: {gcs_uri_source}.")
    context_str = download_blob(gcs_uri_source)

    # Update Instance Id
    context = json.loads(context_str.decode('UTF-8'))
    if 'instance_id' in context:
        logging.debug(f"Assigning {destination_instance_id} as instance_id.")
        context['instance_id'] = str(destination_instance_id)
        context_str = jsonify(context)

    file_name_destination = f"{workflow_id}_v{workflow_version}_{destination_instance_id}.json"
    gcs_uri_destination = f'gs://{bucket_name}/{folder_name}/{file_name_destination}'
    logging.debug(
        f"Trying to upload the following resource: {gcs_uri_destination}.")
    logging.debug(f"Context: {context_str}")
    upload_blob(gcs_uri_destination,
                context_str,
                content_type="application/json")
    return gcs_uri_destination


def jsonify(obj):
    """Make an object as json"""
    return json.dumps(obj, default=utils.json_formatter)


def collect_files_from_bucket(bucket_name, prefix):
    logging.info("Collecting files from {} using as prefix {}".format(bucket_name, prefix))
    client = storage.Client()
    existing_files = [
        "{}".format(blob.name)
        for blob in client.list_blobs(bucket_name, prefix=prefix)
    ]
    return existing_files


def move_blob(bucket_name, blob_name, new_bucket_name, new_blob_name):
    """
    Function for moving files between directories or buckets. it will use GCP's copy 
    function then delete the blob from the old location.

    inputs
    -----
    object containing the following fields:
            bucket_name: name of bucket
            blob_name: str, name of file 
                ex. 'data/some_location/file_name'
            new_bucket_name: name of bucket (can be same as original if we're just moving around directories)
            new_blob_name: str, name of file in new directory in target bucket 
                ex. 'data/destination/file_name'
    """
    
    storage_client = storage.Client()
    source_bucket = storage_client.get_bucket(bucket_name)
    source_blob = source_bucket.blob(blob_name)
    destination_bucket = storage_client.get_bucket(new_bucket_name)
    print("Moving file to bucket {}...".format(destination_bucket))

    # copy to new destination
    new_blob = source_bucket.copy_blob(source_blob, destination_bucket,
                                       new_blob_name)
    # delete in old destination
    source_blob.delete()
    print(
        "Blob {} \n in bucket {} \n copied to blob {}\n in bucket {}.".format(
            source_blob.name,
            source_bucket.name,
            new_blob.name,
            destination_bucket.name,
        ))


def upload2storage_json_error(file_name, destination_path):
    print("... and uploading to {}".format(
        RESPONSE_ERROR_DESTINATION_BUCKET_NAME))
    client = storage.Client()
    bucket = client.get_bucket(RESPONSE_ERROR_DESTINATION_BUCKET_NAME)

    blob = bucket.blob(destination_path + file_name)
    blob.upload_from_filename("/tmp/" + file_name)  # add /tmp/ if in GCP


def store_json_locally(filename, result_json):
    print("Storing json file locally...")
    # Serializing json
    json_object = json.dumps(result_json, indent=4, ensure_ascii=False)

    # Writing to sample.json
    # ADD /tmp/ instead of tmp/
    with open("/tmp/" + filename, "w", encoding='utf-8') as outfile:
        outfile.write(json_object)
