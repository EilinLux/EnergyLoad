from google.cloud import secretmanager_v1beta1 as secretmanager
import json, logging

class Loader:

    def __init__(self, default_encoding='UTF-8'):
        self.default_encoding = default_encoding

    def load(self, project_id, secrets_to_download):
        """Load secret variables from GCP Secret Manager"""

        # Create the GCP Secret Manager client
        secret_manager_client = secretmanager.SecretManagerServiceClient()

        # Prepare Local Secret Store
        local_secret_store = {}

        # For each secret to download, download it
        for secret in secrets_to_download:

            # Set the secret path
            secret_id = secret.get("id")
            secret_version = secret.get("version")
            secret_path = secret_manager_client.secret_version_path(project_id, secret_id, secret_version)

            # Download the secret
            downloaded_secret = secret_manager_client.access_secret_version(secret_path)

            # Decode the secret
            decoded_secret = downloaded_secret.payload.data.decode(self.default_encoding)

            # Objectify the secret and store into the Local Secret Store
            local_secret_store[secret_id] = eval(decoded_secret)

        # Return back the Local Secret Store
        return local_secret_store
