## Python Cloud Run Service - Energy Load

This repository contains a Python service designed to run on Google Cloud Run. It facilitates the secure and reliable transfer of data to E-sight, an external service. The service includes APIs for sending data, receiving error messages, and managing API access (login, logout, user creation/modification).



### Structure

The repository is organized as follows:

- **`app`**: Contains the main application logic.
    - **`controller`**:  Handles business logic and data flow.
    - **`management`**:  Provides administrative functions.
    - **`model`**: Defines data models and structures.
    - **`services`**:  Contains individual service modules.
    - `commons.py`:  Shared utility functions and constants.
    - `user.py`:  Handles user-related operations
    - `validator.py`:  Input validation logic.
- **`handler`**:  Handles HTTP requests and responses.
    - **`routers`**: Defines API endpoints and routing.
        - `loader.py`: Dynamically loads routes.
        - `router.py`:  Handles routing of requests to controllers.
- **`services`**:  Contains external service integrations.
    - **`core`**:  Core service modules.
        - `auth.py`:  Authentication and authorization logic.
        - `base64.py`:  Base64 encoding/decoding utilities.
        - `cloudrun.py`:  Interactions with Google Cloud Run.
        - `cloudsql.py`:  Interactions with Google Cloud SQL.
        - `cloudstorage.py`:  Interactions with Google Cloud Storage.
        - `cloudtasks.py`:  Interactions with Google Cloud Tasks.
        - `esight.py`:  Integration with an external service called 'eSight'.
        - `monitoring.py`:  Monitoring and logging utilities.
        - `secretmanager.py`:  Interactions with Google Secret Manager.
        - `utils.py`:  General utility functions.
        - `uuid.py`:  UUID generation utilities.
- `main.py`:  Entry point for the application.
- `requirements.txt`:  List of Python dependencies.
- `Dockerfile`:  Instructions for building the Docker image.
- `README.MD`:  This file.
- `cloudbuild.yaml`:  Cloud Build configuration for standard deployments.
- `gcloud_build_image`:  Script to build the Docker image using gcloud.


### Usage

This section provides instructions on how to run the service on Cloud Run and interact with its APIs.

#### Prerequisites

Before deploying and using the service, ensure you have the following:

- **Google Cloud Project:** A Google Cloud project with billing enabled.
- **gcloud CLI:** The gcloud command-line tool installed and configured with your project.
- **Docker:** Docker installed and running on your local machine.
- **Service Account:** A service account with the necessary permissions to deploy to Cloud Run and access other GCP resources (e.g., Cloud SQL, Cloud Storage).


#### Deployment

This service is deployed to Cloud Run using Cloud Build. The `cloudbuild.yaml` file defines the build and deployment steps.

**Here's a breakdown of the Cloud Build process:**

1. **Build the Docker Image:**
   - Uses the `gcr.io/cloud-builders/docker` image to build the Docker image for the service.
   - The `Dockerfile` is used to define the image build process:
     ```dockerfile
     FROM python:3.7-slim-stretch

     ENV APP_HOME /app
     WORKDIR $APP_HOME
     COPY app .

     RUN pip install -r requirements.txt
     ENV PORT 8080

     CMD exec gunicorn --bind :$PORT --workers 1 --threads 3 main:app --timeout 0 
     ```
     - This `Dockerfile` starts with a slim Python 3.7 base image.
     - Sets the working directory to `/app`.
     - Copies the application code.
     - Installs dependencies using `requirements.txt`.
     - Exposes port 8080.
     - Uses `gunicorn` to run the application with 1 worker and 3 threads.

2. **Push the Docker Image:**
   - Pushes the built image to Google Container Registry (GCR).

3. **Deploy to Cloud Run:**
   - Deploys the image to Cloud Run using `gcloud run deploy`.
   - Configures the service with:
     - 16GiB of memory
     - 4 CPUs
     - Connection to a Cloud SQL instance
     - A specific service account
     - Required environment variables
     - "techedge" team label

4. **Deploy ESP (Extensible Service Proxy):**
   - Deploys the ESP to Cloud Run to handle API management.
   - Uses the `gcr.io/cloud-builders/gcloud` image with the `endpoints-release/endpoints-runtime-serverless` image for ESP.
   - Allows unauthenticated requests.
   - Configures the ESP with:
     - A specific service account
     - "techedge" team label
     - `ENDPOINTS_SERVICE_NAME` environment variable

5. **Deploy Endpoints:**
   - Deploys the API configuration defined in `openapi.yaml` using `gcloud endpoints services deploy`.

6. **Enable API:**
   - Enables the deployed API.

**Cloud Build Configuration:**

```yaml
steps:
  # ... (Build, Push, Deploy steps as described above) ...

images:
  - gcr.io/$_PROJECT_ID/$_REPO_NAME

options:
  logging: CLOUD_LOGGING_ONLY
```
## API Documentation
This service uses OpenAPI Specification v2.0 to define its API. The swagger.yaml file in this repository provides a detailed description of the API endpoints, request/response schemas, and authentication methods.

### Key points from the API documentation:

* Endpoints: The API exposes endpoints for health checks (/health), user authentication (/login, /logout), user information (/user), sending data to e-Sight (/api/v1/service/send/*), receiving error reports from e-Sight (/api/v1/service/receive/errorjson), and managing users (/api/v1/management/users/*).
* Authentication: Some endpoints require API keys (api_key) while others use JWT authentication (edm_jwt).
* Error Handling: The /api/v1/service/receive/errorjson endpoint allows e-Sight to report errors encountered during data processing.



##### Cloud Endpoints & Extensible Service Proxy V2 (ESPv2)

**Cloud Endpoints**. For security reasons a Cloud Endpoints service was implemented as API management system to secure, monitor, analyze, and set quotas on APIs. Indeed, access control is the most important reason for implementing it, since Cloud Endpoints resource manages who has access to an API as well as establishing rules around how data requests are handled. Cloud Endpoints uses the Extensible Service Proxy V2 (ESPv2) as an API gateway


Extensible Service Proxy V2 (ESPv2) is an Envoy-based proxy, an open-source edge and service proxy designed for cloud-native applications, that enables Cloud Endpoints to provide API management features (such as authentication, monitoring, and logging). ESPv2 container is deployed initially on a prebuilt [Google public images](https://console.cloud.google.com/gcr/images/endpoints-release/GLOBAL/endpoints-runtime-serverless@sha256:018deb3ea57b9c0a7061e81d48eb990056547cfe71d1f95fc1e2647205eccae9/details?tag=2) using ci-cd. On top of the ESPv2 Docker image, a OpenAPI specification (or definition) is what allows the ESPv2 proxy to understand what to do with requests; how to authenticate them and where to send them.



**Notice:** Considering security restrictions, the Google image was required to be in one of the organization project, for this reason, a yaml file with the following steps have been run to pull and push the image to an internal project.

```
    steps:
        -	name: 'gcr.io/cloud-builders/docker'
             args: ['pull','gcr.io/endpoints-release/endpoints-runtime-serverless:2']
        -	name: 'gcr.io/cloud-builders/docker'
            args: ['tag','gcr.io/endpoints-release/endpoints-runtime-serverless:2','gcr.io/$PROJECT_ID/endpoints-release/endpoints-runtime-serverless']
        -	name: 'gcr.io/cloud-builders/docker'
            args: ['push','gcr.io/$PROJECT_ID/endpoints-release/endpoints-runtime-serverless']
    options:
        logging: CLOUD_LOGGING_ONLY
```





**OpenAPI specification**. Endpoints configurations requires to write version 2 OpenAPI Specification, formerly known as the Swagger spec and currently addressed as the industry standard for defining REST APIs. The definitions are written in a .yaml file which describes the openapi version (swagger: '2.0'), the backend service (```x-google-backend```) and any authentication requirements (at the individual api level or at service level).

### API Hardening

This service incorporates multiple layers of security to protect the APIs and ensure authorized access.

#### Load Balancing and DDoS Protection

- **Load Balancer:** Distributes incoming traffic across multiple instances of the application to prevent performance issues and ensure high availability.
- **Cloud Armor:** Provides robust defense against DDoS attacks, safeguarding the service from disruption.

#### Authentication and Authorization

To further enhance security, the following measures are implemented:

- **API Keys:** Each API call requires an API key for authentication. This key is generated in the GCP Credentials section and is associated with each service.
- **JWT (JSON Web Token):**  Except for the `/login` endpoint, all API calls require a valid JWT for authorization. This adds an extra layer of security by verifying user identity.
- **Role-Based Access Control:** A system of roles restricts API access based on user type, ensuring that users only have access to the resources they need.

#### API Key Enforcement

API key enforcement is implemented through the OpenAPI specification. The following snippet is added to each API path definition to require an API key:


```
    security:

    - api_key: [ ]
```
To be notice that except for the /login API, all the other APIs require a JSON Web Token (JWT) in addition to the APIkey.

```
    security:

    -	api_key: []

    -	edm_jwt: []
```
In order to create a private key, which has to be associated to a specific account, it is necessary to go to IAM service > service account > select the specific account > click on KEY tab > create new key.



This is a JSON file which contains the following information.


```
    {
        "type": "service_account",
        "project_id": " project_id_name",
        "private_key_id": "# the APIKEY",
        "private_key": "-----BEGIN PRIVATE KEY-----\nLONGHASHCODE\n-----END PRIVATE KEY-----\n",
        "client_email": "service_account_name@project_id_name.iam.gserviceaccount.com",
        "client_id": "service_account_number",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url":
        "https://www.googleapis.com/robot/v1/metadata/x509/service_account_name%40project_id_name.iam.gserviceaccoun
            t.com"
    }

```

In the pre-dev, this was done using the App Engine default service account and the APIKEY was used to authenticate as follow: ```https://service.com/login?key=APIKEY```. The whole file was saved to Secret Manager, as ```_SERVICE_ACCOUNT_JWT_SECRET```.


#### JSON Web Token (JWT).
In addition to an ApiKey, except for the ```/login``` API, every other API request requires an additional level of security, ie. a JSON Web Token (JWT). A JWT is open and standard RFC 7519, used to identify a user without having to send private credentials on every request.

In both the edm-sight-send-apis and the edm-sight-receive-apis CloudRun:
* JWT are created using the /login api
* JWT are set to be 3600 seconds valid.  In case, it is needed to invalidate the JWT token before the ending of 3600 seconds, it is possible to use the /logout api.
* Each time a JWT is used in an API, a validate_jwt function is used to check if the JWT is not present in the jwt table where the /logout api writes, once an users wants to log out before the end of the 3600 seconds. If the JWT is still valid, the request is elaborated.



#### MySQL Database.

Following Security requirements, a separated database to monitor access to and store Credentials and Roles for the APIs was implemented. The service chosen on GCP was Cloud SQL which manage relational data for MySQL, PostgreSQL, and SQL Server.

**Monitoring access to the API**. To monitor the access to the APIs a log table has been created on a MySQL DB, called edm-cloudmysql-instance. The following events are logged to the table:

* a) successful logins (log-in and out)

* b)	failed login attempts

* c)	violations of access restrictions

* d)	creation or modification of user accounts



And for each logged event the following data are collected:

* a)	time and date at which the event took place
* b)	type of event 
* c)	IP address of the origin 
* d)	MSISDN of the origin 
* e)	user ID


**Manual Implementation**. Even though in dev and production environment the service was terraformed, in the pre-dev environment the following manual steps were required:

1)	Created a MySQL instance manually using the user-interface (UI). The minimum required parameter to set are

   ```
    Name: edm-cloudmysql-instance
    Password: EDM-password!
    Config: Deployment
    Region: Europe-west1
    ```


2)	Enable Cloud SQL admin API


3)	Added ```-add-cloudsql-instances _INSTANCE_CONNECTION_NAME``` to yaml, where is ```_INSTANCE_CONNECTION_NAME``` is of the type ```project:region:instancename``` and is defined at the cloud build level.

**Useful commands for the command line or SDK:**

- set up the default project: ```gcloud config set project tst-nwp-live```
- connect to DB instance using a specific user (you need to enter the associated password to the user to authenticate ```gcloud sql connect edm-cloudmysql-instance --user=root```

**Useful SQL commands for SQL console, after authentication [steps above]:**
-	create a new database in the Cloud SQL ```CREATE DATABASE `edm-db-workflows`;```
- use an existing database in the Cloud SQL ```USE edm-db-workflows;```
- 	create a table with schema in the ```USE database``` and 
```CREATE TABLE user_auth_roles (id VARCHAR(50), username VARCHAR(15), password VARCHAR(150), type VARCHAR(250), creator VARCHAR(500), status VARCHAR(25));```
- insert values into an existing table in the USE database ```INSERT INTO user_auth_roles VALUES("xxxxxxxxxx","edmusername", "$argon2id$v=19$m=102400,t=2,p=8$xxxxxxxxxxxxxxxxxxxxxxxxxxx", "root", "active");```

**Credentials and roles.**  The APIs usage was designed to have different levels of accessibility. As already mentioned, the usage of APIs was meant to be for the client as much as for externals (e-sight service). For this reason, the APIs required a authentication layer and the MySQL has been chosen as solution to stores the credentials for users that have to interact with the APIs and their roles in the ```user_auth_roles``` table.


**ci-cd, cloud build trigger and yaml file**. To use the mentioned service the yaml file required to have the ```--add-cloudsql-instances``` followed by the ```$_CLOUD_SQL_INSTANCE_CONNECTION_NAME``` to connect the Cloud Run to the MySQL instance23. The ```$_CLOUD_SQL_INSTANCE_CONNECTION_NAME``` is defined at the Cloud build trigger level and contains the connection name as follow project:region:instancename. The name of the connaction was added also to the environmental variables using the argument ```--set-env-vars```.
