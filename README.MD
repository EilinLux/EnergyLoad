## Table of contents
* [General info](#general-info)
* [Deploying cycle, Ci-Cd and DevOps cycle](#Deploying-cycle-Ci-Cd-and-DevOps-cycle)
* [Ni-fi connection to store emails in .msg format to GCP buckets.](#Ni-fi-connection-to-store-emails-in-.msg-format-to-GCP-buckets)
* [Raw Data Storage (Extraction)](#Raw-Data-Storage-(Extraction))
* [Data Processing in GCP (Transformation)](#-Data-Processing-in-GCP-(Transformation))
* [Data Distribution Service for E-sight (Loading)](#Data-Distribution-Service-for-E-sight-(Loading))


## General info

This repo represents the code related to [Data Distribution Service for E-sight (Loading)](#Data-Distribution-Service-for-E-sight-(Loading)) which is the third part of a bigger project that concerns an energy solution to track and improve power consumption and required

1)	the implementation of an ETL pipeline. The data are registered by sensors and sent to email boxes, then a Ni-fi collects the data and move them to Cloud Storage (CS). The finalization of an object on the CS bucket triggers a pipeline composed by two cloud functions to extract and transform the data into a suitable format for e-sight. The data sending to e-sight is performed daily at midnight (UTC) using a set of APIs implemented on the client side that interact with the one that e-sight provides. The main features of the deployed APIs on the client side are:
 
    -	send the data collected on GCP about the consumptions to e-sight.

    -	receive messages from e-sight in case of error since e-sight validates the content of the json files asynchronously.

2) the monitoring of the process through a dashboard. For this reason, on the data engineering side, a data storage on Big Query was implemented in order to have visibility on the processing that were taking place along the pipeline process. For each step performed on GCP, whenever an object is processed (either successfully or not) in one of these steps (either extract, transform, or APIs) at least a record is registered to a specific table. On the other side the data visualization team implemented a dashboard to allow reliability and observability of the flow.
 [IMAGE]


##### Terminology

The data sources are called in this project data feeds, up to the time this documentation is written, 3 data feeds ETL pipeline have been implemented, since each data feed sends the data in a different format that need to be uniformed to the e-sight template.

Each data source sends data regarding different countries, which within the project are called **local markets**. Local markets are abbreviated in with two capital letters (ex. Germany is abbreviated DE).
 

Additional information mentioned in this documentation and that can be not easily deduce regards siteId and meterId. The **meterId** is the unique identifier associated to the devices that measures the amount of energy consumption. The **siteId** is the unique identifier of a specific site, intended as an area of ground on which a meter stands, and not as an amount of heat and electricity consumed by a building as reflected in your utility bills. For each site there could be more than one meter. However, not all data feeds have a siteId, in this case the meterId is not associated to any meterId. However, if the siteId is present, it has to be stored with the rest of the data.


## Deploying cycle, Ci-Cd and DevOps cycle

**Deploying cycle**. The usage of three type of environment (pre-dev, dev and prod) allows teams to build, test, and deploy products in different phases to ensure high quality products for their users.

As data engineer, the main project to deploy on was energy-tst-predev. Each sprint (two weeks) a mvp was presented. If approved, it would have been moved to dev environment for being tested, once it would have received the approval by the testing team, it would have been deployed on production.

**DevOps cycle**. it is indeed composed by the various phases of continuous integration, continuous delivery, continuous testing, and continuous monitoring.

**ci-cd**. In software engineering, it is the combined practices of continuous integration and continuous delivery or continuous deployment.

In our case the two following applies:

- **continuous integration** as the practice of merging all developers' working copies to a shared mainline as often as possible.

- **continuous delivery** as the practice of automatically deploy all code changes to a testing and/or production environment after the build stage.

The following steps need to be performed on the client projects (each of them), in order to set up a ci-cd pipeline for the Cloud Functions(*) and the APIs running on Cloud Run (**):

❖	Enable APIs for GCP services:
* Cloud Function *
* Cloud Run **
*	Cloud Build
*	Service Management **
*	Service Control API**
*	Google Cloud Endpoints**
*	Cloud SQL**
*	Service Usage API**

❖	Repo on GitHub: Create or have a Repo on GitHub

❖	SA permissions: Grant the right permissions to one or more service account (SA)
*	App Engine Admin
*	Cloud Build Service Account
*	Cloud Build Worker Pool user
*   Service Account User
*	Object and Storage Admin
*	Cloud Functions Developer*
*	Cloud Run Admin**
*	Service Management Administrator **
*	Service Usage Admin**
*	Endpoints Portal Service Agent
*	Service Consumer**

❖	Whitelist SA(s): whitelist the compute service account18

❖	Set up a Worker: Create a private pool (set up a worker)

❖	Created a GitHub Connector: Create a connector between the project and the repo on GitHub

❖	Created a VPC connector on GCP19: Create a VPC connector

❖	Trigger: Set a trigger on CloudBuild

❖	Yaml: Set up the right config in a yaml file in the GitHub repo at the root level


**Notice** In case a Virtual Private Cloud (VPC) network is used, it requires to set the location for the Private pool, the connector, the trigger and yaml config to be the same. As already mentioned, europe-west1 was been chosen as location for all the resources in this project.


In order to automatically deploy all code changes to one of the environments

1.	commits the source code to GitHub on the repos set up in Cloud Build and the specified branch name.

2.	GitHub triggers a post-commit hook to Cloud Build.

3.	Cloud Build creates the container image and pushes it to Container Registry.

4.	Cloud Build notifies to a service (ex. Cloud Run) to roll out a new deployment.

5.	The service (ex. Cloud Run) pulls the image and runs it.

## Ni-fi connection to store emails in .msg format to GCP buckets


Apache Ni-Fi is an integrated data logistics platform for automating the movement of data between disparate systems. In EDM project, Ni-Fi works as a middleware to automatically move the emails from the mailboxes to GCP. The Ni-Fi connects to the mail server at a regular frequency and store the messages temporarily on an edge node, then it pushes them to GCP using a dedicated Service Account from GCP.

Metadata and attachments are stored to e-test-dh-edm-rawingested in their original format (.msg) without any further transformation. The path is partitioned by DataFeed, which is the name given to the data source, the year, the month and the day, i.e. ```DataFeed/year/month/day```.

The	data are sent in different formats depending on data feed type as email attachments to the email boxes. Depending on the data feed type, data are fetched at different frequency and have different sizes.

|Data Feed|File format|	AVG Size (MB)|	Frequency|
 |--- |--- |--- |--- |
|DataFeed1	| csv |	0,002	|1200+| emails/day|
 |--- |--- |--- |--- |			
|DataFeed2|	xlsx|0,122	|4 |emails/day|
 |--- |--- |--- |--- 			
|DataFeed3|	zipped|	0,001|4| emails/day|
|--- |--- |--- |--- |		


The fact that each file is partitioned, it is important for data management and access, since it reduce contention, improve scalability and optimize performance (ex. in data retrieval). In addition, the fact that the data are partitioned by data feed, it is important for triggering the right cloud function.


**Partition** is based on folder partition, not bucket partition. The suggestion of using one bucket for each data feed was refused by the client without any further specification. This would have reduced the costs considering that all the extract cloud functions activate one whichever object is finalized on e-test-dh-edm-rawingested. However, the first check done by the cloud function is checking the data feed type folder, so that the process is killed for all the function except the one that contains the right function for the data extraction of the specific type of data feed. Same process applies to all transform cloud functions


## Raw Data Storage (Extraction)

##### 1.1 Overview


As already mentioned, for each data feed (i.e. data source) a specific cloud function was implemented, following the naming convention<use-case>-<data-feed-type>-<action>, but pursuit the same purpose as long as the <action> tag is the same.

An edm-<data-feed-type>-extract cloud function extracts the email attachment and useful metadata as soon as a file is finalized on e-test-dh-edm-rawingested. The status of the process is monitored in e-bqt-edm-monit-raw table, in case of errors or warnings addition info are available on e-bqt-edm-monit-raw-error table.


#### 1.2 Data Flow

**Success**. If the process is successful, the file attachment is collected, associate with the correct sent datetime stamp (in case of DataFeed1 also with the site_id which is stated in the email title) and stored to e-test-dh-edm-rawprepared bucket in a folder which has the following partitioned path ```DataFeedType/LocalMarket/year/month/day``` and has the following file name ```datafeed_localmarket_sentmessagetimestamp__siteid_siteId_title_emailTitle___attachment```

path example: ```DataFeed1/DE/2022/06/15```

file name example: ```DataFeed1_De_2022-03-22_151137000000__siteid_H9509_title_H9509LogdatenCore___historyExport.csv```

**Notice**: in case of zipped files (ex. RWE) the file renamed is only the zip one, the process of extraction takes place in the edm-<data-feed-type>-transform cloud function.

**Error**. If the process is not successful, the file is moved to ```e-test-dh-edm-error``` in a folder with the following path ```extract/<category_error>/<original_path>``` without any further change.



**Monitoring**. For each file process, identified by a uuid, a new line is added to e-bqt-edm-monit-raw table, under the e_test_bqd_edm_monitoring dataset (no matter if it is successful or not). If the process is not successful, additional information about the file and the process are collected for the monitoring dashboard on e-bqt-edm-monit-raw-error.
 


## Data Processing in GCP (Transformation)

##### 2.1 Overview


As already mentioned, for each data feed (i.e. data source) a specific cloud function was implemented, following the naming convention<use-case>-<data-feed-type>-<action>, but pursuit the same purpose as long as the <action> tag is the same.


An edm-<data-feed-type>-transform cloud function process data and save them in a json format as soon as a file is finalized on e-test-dh-edm-rawprepared. The status of the process in monitored in e-bqt-edm-monit-processed, in case of errors or warnings addition info are available on e-bqt-edm-monit-processed-error.

[Figure 3- Transformation]

**Success**. If the process is successful, the data are transformed and saved in a JSON format on e-test-dh-edm-processed. Each data feed requires different type of transformations, however there are also some transformations common to all data feeds are:

1.	Timestamp conversion to UTC: all files timestamps should be converted UTC time zone, since normally files are coming from different countries with different timestamps for the sake of comparative analysis.

2.	Decimal conversion: normalize files so that all use dots as decimal separator.

3.	messageId generation: messageId is a unique identifier of the file, in each file the energy consumption, should refer to that specific data feed, local marker, meter id and day and has the following format: ```data_feed_type_local_market_meter_id_date_stamp```. 
Example. ```DataFeed1_De_/L_SSV/L_SSV0101/P_ELT_LC_2022_06_07```

**Notice**: if a file for the same meterId and for the same day has already been created, the records are appended to the existing file, otherwise a new file is created.



Data are stored to e-test-dh-edm-rawingested bucket in a folder which has the following path:
```DataFeedType/LocalMarket/year/month/day```

ex. ```DataFeed1/DE/2022/06/15```

and has the following file name:

```datafeed_localmarket_sentmessagetimestamp__siteid_siteId_title_emailTitle___attachment__meterId```

ex. ```DataFeed1_De_2022-03-22_151137000000__siteid_H9509_title_H9509LogdatenCore___historyExport.csv____L_SSV_L_SSV0101_P_ELT_LC```

The output file is in JSON format, the data are aggregated by meterId and day (one JSON message containing data for only one meter for each day) in a suitable format to eSight.

Example.

    
    {
    "messageType": "dataUpdate",
    "header": {
    "gatewayTypeUrn": "urn:esight:assets:edm:De:DataFeed1",
    "messageId": "De_DataFeed1_/L_SSV/L_SSV0102/P_ELT_SYP_2022_06_07",
    "version": null,
    "gatewayUrn": "urn:esight:assets:edm:H9509:/L_SSV/L_SSV0102/P_ELT_SYP"
    },
    "gatewayData": {
    "datapointValues": [
    
    {
    "datapointKey": "NA",
    "value": "11406.0",
    "tsIso8601": "2022-03-22T12:00:00Z"
    },
    {
    "datapointKey": "NA",
    "value": "11188.0",
    "tsIso8601": "2022-03-22T13:00:00Z"
    },
    {
    "datapointKey": "NA",
    "value": "11188.0",
    "tsIso8601": "2022-03-22T14:00:00Z"
    },
    {
    
    "datapointKey": "NA",
    "value": "11188.0",
    "tsIso8601": "2022-03-22T15:00:00Z"
    }
    ]
    }
    }
     
**Error**. If the process is not successful, the file is moved to e-test-dh-edm-error in a folder with the following path ```transform/<category_error>/<original_path>``` without any further change.


**Monitoring**. For each file process, identified by a uuid, a new line is added to e-bqt-edm-monit- processed table, under the ```e_test_bqd_edm_monitoring``` dataset (no matter if it is successful or not). If the process is not successful, additional information about the file and the process are collected for the monitoring dashboard on ```e-bqt-edm-monit-raw-error```.

## Data Distribution Service for E-sight (Loading)

##### 3.1.2 Load Balancer & Cloud Armor

**Load Balancer**. A load balancer distributes user traffic across multiple instances of your applications. By spreading the load, load balancing reduces the risk that your applications experience performance issues. 

**Google Cloud Armor**. Google Cloud Armor is an enterprise-grade DDoS defence service and Web Application Firewall. That means that it can help protect HTTP-frontend applications from both targeted and distributed denial of service attacks. 

##### 3.1.3 Cloud Endpoints & Extensible Service Proxy V2 (ESPv2)

**Cloud Endpoints**. For security reasons a Cloud Endpoints service was implemented as API management system to secure, monitor, analyze, and set quotas on APIs. Indeed, access control is the most important reason for implementing it, since Cloud Endpoints resource manages who has access to an API as well as establishing rules around how data requests are handled. Cloud Endpoints uses the Extensible Service Proxy V2 (ESPv2) as an API gateway
 

Extensible Service Proxy V2 (ESPv2) is an Envoy-based proxy, an open-source edge and service proxy designed for cloud-native applications, that enables Cloud Endpoints to provide API management features (such as authentication, monitoring, and logging). ESPv2 container is deployed initially on a prebuilt [Google public images](https://console.cloud.google.com/gcr/images/endpoints-release/GLOBAL/endpoints-runtime-serverless@sha256:018deb3ea57b9c0a7061e81d48eb990056547cfe71d1f95fc1e2647205eccae9/details?tag=2) using ci-cd. On top of the ESPv2 Docker image, a OpenAPI specification (or definition) is what allows the ESPv2 proxy to understand what to do with requests; how to authenticate them and where to send them.

**Notice:** Considering security restrictions, the Google image was required to be in one of the organization project, for this reason, a yaml file with the following steps have been run to pull and push the image to an internal project.

    steps:
        -	name: 'gcr.io/cloud-builders/docker'
             args: ['pull','gcr.io/endpoints-release/endpoints-runtime-serverless:2']
             
        -	name: 'gcr.io/cloud-builders/docker'
            args: ['tag','gcr.io/endpoints-release/endpoints-runtime-serverless:2','gcr.io/$PROJECT_ID/endpoints-release/endpoints-runtime-serverless']
        
        -	name: 'gcr.io/cloud-builders/docker'
            args: ['push','gcr.io/$PROJECT_ID/endpoints-release/endpoints-runtime-serverless']
    options:
        logging: CLOUD_LOGGING_ONLY



**OpenAPI specification**. Endpoints configurations requires to write version 2 OpenAPI Specification, formerly known as the Swagger spec and currently addressed as the industry standard for defining REST APIs. The definitions are written in a .yaml file which describes the openapi version (swagger: '2.0'), the backend service (```x-google-backend```) and any authentication requirements (at the individual api level or at service level).


##### 3.1.4 Cloud Run & APIs Backend

APIs backend. The APIs have two main services: one for sending data to e-sight and the other for receiving error messages in case of failure.

As for the sending, every day at midnight a Cloud Scheduler, called edm e-sight-send-scheduler, send a pub-sub topic, called edm-e-sight-send-pubsub, which triggers edm-sight-send-apis image that is hosted on CloudRun. This api collects all the files in the processed bucket, e-test-dh-edm-processed. and send them to e-sight.

As for receiving e-sight asynchronous responses in case of failure, the responses are redirected to an api hosted on edm-sight-receive-apis. This api

1)	extracts the useful information from the response adding them to a table inBig Query

2)	save the original file to Cloud Storage in a Json format.

An addition set of APIs has been implemented to manage the APIs access (such as login, logout, create a new account, edit an existing one, deactivate one).
 

### 3.2 Overview on hardening APIs

In addition to the already mentioned service Cloud Amour and Load Balancer, the architecture offers the following hardening feaures: the mandatory usage of APIKey in every API call, the mandatory usage of a JSON Web Token in every API call (except ```/login```), a system of roles to restrict the APIs access based on user type.

##### 3.2.1 APIkey.

An application programming interface (API) key is a code used to identify an application or user and is used for authentication in computer applications. In the architecture an Apikey is generated in the Credentials sections on GCP and is associated to each service (the one for sending and the one for receiving). The mandatory usage of APIkey was added to all the APIs call using the OpenAPI specification, in particular by adding to each path the following:

    
    security:
    - api_key: [ ]

To be notice that except for the /login API, all the other APIs require a JSON Web Token (JWT) in addition to the APIkey.


    security:
    -	api_key: []
    -	edm_jwt: []



In order to create a private key, which has to be associated to a specific account, it is necessary to go to IAM service > service account > select the specific account > click on KEY tab > create new key.

This is a JSON file which contains the following information.

    
    {
        "type": "service_account",
        "project_id": " project_id_name",
        "private_key_id": "741673a367892fc6d18ba0452b9320343fbb009b", # the APIKEY
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


In the pre-dev, this was done using the App Engine default service account and the APIKEY was used to authenticate as follow: ```https://service.com/login?key=APIKEY```. The whole file was saved to Secret Manager, as ```_SERVICE_ACCOUNT_JWT_SECRET```.

 
##### 3.2.2 JSON Web Token (JWT).

In addition to an ApiKey, except for the ```/login``` API, every other API request requires an additional level of security, ie. a JSON Web Token (JWT). A JWT is open and standard RFC 7519, used to identify a user without having to send private credentials on every request.

In both the edm-sight-send-apis and the edm-sight-receive-apis CloudRun:
* JWT are created using the /login api
* JWT are set to be 3600 seconds valid.  In case, it is needed to invalidate the JWT token before the ending of 3600 seconds, it is possible to use the /logout api.
* Each time a JWT is used in an API, a validate_jwt function is used to check if the JWT is not present in the jwt table where the /logout api writes, once an users wants to log out before the end of the 3600 seconds. If the JWT is still valid, the request is elaborated.



#####  3.1.5 MySQL Database.
 
Following Security requirements, a separated database to monitor access to and store Credentials and Roles for the APIs was implemented. The service chosen on GCP was Cloud SQL which manage relational data for MySQL, PostgreSQL, and SQL Server.

Monitoring access to the API. To monitor the access to the APIs a log table has been created on a MySQL DB, called edm-cloudmysql-instance. The following events are logged to the table:
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
 



MANUAL IMPLEMENTATION. Even though in dev and production environment the service was terraformed, in the pre-dev environment the following manual steps were required:
1)	Created a MySQL instance manually using the user-interface (UI). The minimum required parameter to set are

    ```Name: edm-cloudmysql-instance```
   ``` Password: EDM-password!```
    ```Config: Deployment```
    ```Region: Europe-west1```

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

**Credentials and roles.**  The APIs usage was designed to have different levels of accessibility. As already mentioned, the usage of APIs was meant to be for the client as much as for externals (e-sight service). For this reason, the APIs required a authentication layer and the MySQL has been chosen as solution to stores the credentials for users that have to interact with the APIs and their roles in the ```user_auth_roles``` table.


**ci-cd, cloud build trigger and yaml file**. To use the mentioned service the yaml file required to have the ```--add-cloudsql-instances``` followed by the ```$_CLOUD_SQL_INSTANCE_CONNECTION_NAME``` to connect the Cloud Run to the MySQL instance23. The ```$_CLOUD_SQL_INSTANCE_CONNECTION_NAME``` is defined at the Cloud build trigger level and contains the connection name as follow project:region:instancename. The name of the connaction was added also to the environmental variables using the argument ```--set-env-vars```.
 
