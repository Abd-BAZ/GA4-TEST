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

# Function to fetch GA-4 data
def fetch_ga4_data(client, property_id):
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
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")]  # Adjust date range as needed
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

        logging.info("GA-4 data fetched successfully.")
        return report_data
    except Exception as e:
        logging.error(f"Error fetching GA-4 data: {e}")
        return []

# Routes for your existing pages
# Add these routes to fetch GA4 data for Home, About, and FAQ pages
@app.route("/ga4-data-home")
def ga4_data_home():
    return fetch_ga4_data_for_page("/home")

@app.route("/ga4-data-about")
def ga4_data_about():
    return fetch_ga4_data_for_page("/about")

@app.route("/ga4-data-faq")
def ga4_data_faq():
    return fetch_ga4_data_for_page("/faq")


# Helper function to fetch data for a specific page
def fetch_ga4_data_for_page(page_path):
    try:
        # Initialize the GA-4 client
        client = initialize_analytics_reporting()

        # Fetch the GA-4 data
        property_id = os.getenv("GA4_PROPERTY_ID", "473956527")  # Replace with your property ID
        data = fetch_ga4_data(client, property_id, page_path)

        # Return the data as JSON
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error fetching data for {page_path}: {e}")
        return jsonify({"error": "Failed to fetch GA-4 data"}), 500


# Update the fetch_ga4_data function to accept a page_path parameter
def fetch_ga4_data(client, property_id, page_path):
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                {'name': 'date'},
                {'name': 'pagePath'}
            ],
            metrics=[
                {'name': 'activeUsers'},
                {'name': 'screenPageViews'},
                {'name': 'eventCount'}
            ],
            dimension_filter={
                "filter": {
                    "field_name": "pagePath",
                    "string_filter": {"value": page_path}
                }
            },
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")]
        )

        response = client.run_report(request)

        report_data = [
            {
                "date": row.dimension_values[0].value,
                "pagePath": row.dimension_values[1].value,
                "activeUsers": int(row.metric_values[0].value),
                "pageViews": int(row.metric_values[1].value),
                "eventCount": int(row.metric_values[2].value),
            }
            for row in response.rows
        ]
        return report_data
    except Exception as e:
        logging.error(f"Error fetching GA4 data: {e}")
        return []