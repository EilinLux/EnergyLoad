from google.cloud import secretmanager_v1beta1 as secret_manager


def download(secrets, project_id, encoding):
    """Load secret variables from GCP Secret Manager."""

    # Create the GCP Secret Manager client
    secret_manager_client = secret_manager.SecretManagerServiceClient()

    # Prepare Local Secret Store
    secret_store = {}

    # For each secret to download, download it
    for secret in secrets:

        # Set the secret path
        secret_id = secret.get("id")
        secret_version = secret.get("version")
        secret_path = secret_manager_client.secret_version_path(
            project_id, secret_id, secret_version)

        # Download the secret
        downloaded_secret = secret_manager_client.access_secret_version(
            secret_path)

        # Decode the secret
        decoded_secret = downloaded_secret.payload.data.decode(encoding)

        # Objectify the secret and store into the Local Secret Store
        secret_store[secret_id] = eval(decoded_secret)

    # Return back the Local Secret Store
    return secret_store


def download_single(secret_id, secret_version, project_id, encoding):
    """Load secret from GCP Secret Manager."""

    # Create the GCP Secret Manager client
    secret_manager_client = secret_manager.SecretManagerServiceClient()

    # Build the secret path
    secret_path = secret_manager_client.secret_version_path(
        project_id, secret_id, secret_version)

    # Download the secret
    downloaded_secret = secret_manager_client.access_secret_version(
        secret_path)

    # Decode the secret
    decoded_secret = downloaded_secret.payload.data.decode(encoding)

    return decoded_secret
