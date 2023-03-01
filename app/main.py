from flask import Flask
from flask_cors import CORS
from handler.router import Router
from handler.loader import Loader
import os
import logging

app = Flask(__name__)
CORS(app)
logging.getLogger().setLevel(logging.DEBUG)

# Set essential variables
default_encoding = 'UTF-8'
project_id =  os.environ.get("_PROJECT_ID")
main_db_secret =  os.environ.get("_MAIN_DB_SECRET")



# Set secrets to download
secrets_to_download = [
    {
        "id": main_db_secret,
        "version": "latest"
    }
    # Add here other secrets to download...
    # {"id":cloud_storage_secret, "version":"latest"}
]

# Get the Local Secret Store
local_secret_store = Loader(default_encoding).load(project_id,
                                                   secrets_to_download)

# Configure Routing
Router(app, local_secret_store)

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
