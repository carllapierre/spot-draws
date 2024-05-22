import os

from application.constants import AppInfo
from flask import Flask
from flask_cors import CORS

# Create the application
app = Flask(AppInfo.NAME)

# Set secret key
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret!")

# Setup cors
cors = CORS(app)
