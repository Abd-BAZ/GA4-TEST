from flask import Flask, render_template, jsonify
import os
import json
import logging
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange
# from flask_caching import Cache

app = Flask(__name__)

# Configure caching
# cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})  # 5 minutes

# Set up logging
logging.basicConfig(level=logging.INFO)

# Validate environment variables
if not os.getenv("GA4_CREDENTIAL_JSON") or not os.getenv("GA4_PROPERTY_ID"):
    logging.error("Required environment variables (GA4_CREDENTIAL_JSON, GA4_PROPERTY_ID) are not set!")
    exit(1)

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
def fetch_ga4_data(client, property_id, page_path, start_date="7daysAgo", end_date="today"):
    try:
        # Set up the query request
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                {'name': 'date'},       # Date of activity
                {'name': 'pagePath'},   # Tracks activity per page
                {'name': 'browser'}     # Browser used by users
            ],
            metrics=[
                {'name': 'activeUsers'},       # Active users
                {'name': 'screenPageViews'},  # Total page views
                {'name': 'eventCount'}        # Total events (e.g., downloads)
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],  # Use provided date range
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
                "browser": row.dimension_values[2].value,  # Browser
                "activeUsers": int(row.metric_values[0].value),  # Active users
                "pageViews": int(row.metric_values[1].value),   # Page views
                "eventCount": int(row.metric_values[2].value)   # Events (e.g., downloads)
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
@app.route("/ga4-summary-<section>")
@cache.cached(timeout=300)  # Cache this route for 5 minutes
def ga4_summary_section(section):
    try:
        # Map section to corresponding page paths in GA4
        page_paths = {
            "home": "/",
            "about": "/about",
            "faq": "/faq"
        }
        if section not in page_paths:
            return jsonify({"error": "Invalid section specified"}), 400

        # Initialize the GA-4 client
        client = initialize_analytics_reporting()

        # Fetch summarized data for daily, monthly, and yearly views
        property_id = os.getenv("GA4_PROPERTY_ID", "473956527")  # Use environment variable or default

        # Daily data
        daily_data = fetch_ga4_data(client, property_id, page_paths[section], "7daysAgo", "today")

        # Monthly data (last 30 days)
        monthly_data = fetch_ga4_data(client, property_id, page_paths[section], "30daysAgo", "today")

        # Yearly data (last 365 days)
        yearly_data = fetch_ga4_data(client, property_id, page_paths[section], "365daysAgo", "today")

        # Summarize the data
        def summarize(data):
            if not data:
                return {
                    "activeUsers": 0,
                    "pageViews": 0,
                    "eventCount": 0
                }
            return {
                "activeUsers": sum(stat["activeUsers"] for stat in data),
                "pageViews": sum(stat["pageViews"] for stat in data),
                "eventCount": sum(stat["eventCount"] for stat in data)
            }

        summary = {
            "daily": summarize(daily_data),
            "monthly": summarize(monthly_data),
            "yearly": summarize(yearly_data)
        }

        # Return the summarized data as JSON
        return jsonify(summary)
    except Exception as e:
        logging.error(f"Error in /ga4-summary-{section} route: {e}")
        return jsonify({"error": f"Failed to fetch GA-4 summary data: {str(e)}"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)