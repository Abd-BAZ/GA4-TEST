from flask import Flask, render_template, jsonify
import os
import json
import logging
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Function to initialize Google Analytics Data API client
def initialize_analytics_reporting():
    try:
        # Get the credentials JSON from the environment variable
        credentials_json = os.getenv("GA4_CREDENTIAL_JSON")
        if not credentials_json:
            raise Exception("GA4_CREDENTIAL_JSON environment variable not set!")

        # Load credentials from the JSON string
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json),
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )

        # Initialize the Analytics Data API client
        client = BetaAnalyticsDataClient(credentials=credentials)
        logging.info("Google Analytics client initialized successfully.")
        return client
    except Exception as e:
        logging.error(f"Error initializing GA client: {e}")
        raise

# Function to fetch GA-4 data for a specific page
def fetch_ga4_data(client, property_id, page_path):
    try:
        # Set up the query request
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                {'name': 'date'},       # Date of activity
                {'name': 'pagePath'}   # Tracks activity per page
            ],
            metrics=[
                {'name': 'activeUsers'},       # Active users
                {'name': 'screenPageViews'},  # Total page views
                {'name': 'eventCount'}        # Total events (e.g., downloads)
            ],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],  # Adjust date range as needed
            dimension_filter={
                'filter': {
                    'field_name': 'pagePath',
                    'string_filter': {
                        'match_type': 'EXACT',
                        'value': page_path
                    }
                }
            }
        )

        # Run the query
        response = client.run_report(request)

        # Process the response data
        report_data = []
        for row in response.rows:
            data = {
                "date": row.dimension_values[0].value,  # Date
                "pagePath": row.dimension_values[1].value,  # Page path
                "activeUsers": int(row.metric_values[0].value),  # Active users
                "pageViews": int(row.metric_values[1].value),   # Page views
                "eventCount": int(row.metric_values[2].value)  # Events (e.g., downloads)
            }
            report_data.append(data)

        logging.info(f"GA-4 data fetched successfully for page: {page_path}")
        return report_data
    except Exception as e:
        logging.error(f"Error fetching GA-4 data for page {page_path}: {e}")
        return []

# Routes for static pages
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/live-stats")
def live_stats():
    return render_template("live_stats.html")

# Routes for dynamic GA4 data fetching
@app.route("/ga4-data-<section>")
def ga4_data_section(section):
    try:
        # Map section to corresponding page paths in GA4
        page_paths = {
            "home": "",
            "about": "/about",
            "faq": "/faq"
        }
        if section not in page_paths:
            return jsonify({"error": "Invalid section specified"}), 400

        # Initialize the GA-4 client
        client = initialize_analytics_reporting()

        # Fetch GA-4 data for the specific page
        property_id = os.getenv("GA4_PROPERTY_ID", "473956527")  # Use environment variable or default
        data = fetch_ga4_data(client, property_id, page_paths[section])

        # Return the data as JSON
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error in /ga4-data-{section} route: {e}")
        return jsonify({"error": "Failed to fetch GA-4 data"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
