from flask import Flask, render_template, jsonify
import os
import json
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange

app = Flask(__name__)

# Function to initialize Google Analytics Data API client
def initialize_analytics_reporting():
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
    return client

# Function to fetch GA-4 data
def fetch_ga4_data(client):
    property_id = '473956527'  # Replace with your Google Analytics Property ID

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
            "activeUsers": row.metric_values[0].value,  # Active users
            "pageViews": row.metric_values[1].value,   # Page views
            "eventCount": row.metric_values[2].value  # Events (e.g., downloads)
        }
        report_data.append(data)

    return report_data

# Routes for your existing pages
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

# Route to fetch GA-4 data
@app.route("/ga4-data-json")
def ga4_data_json():
    # Initialize the GA-4 client
    client = initialize_analytics_reporting()

    # Fetch the GA-4 data
    data = fetch_ga4_data(client)

    # Return the data as JSON
    return jsonify(data)

# Route for the live statistics page
@app.route("/live-stats")
def live_stats():
    return render_template("live_stats.html")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)