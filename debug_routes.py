import os
import json
from flask import Blueprint

debug_blueprint = Blueprint("debug", __name__)

@debug_blueprint.route("/check-env")
def check_env():
    try:
        credentials_json = os.getenv("GA4_CREDENTIAL_JSON")
        if not credentials_json:
            return "Environment variable GA4_CREDENTIAL_JSON not found!", 500
        return json.dumps(json.loads(credentials_json))  # Return the parsed credentials for testing
    except Exception as e:
        return f"Error: {e}", 500
