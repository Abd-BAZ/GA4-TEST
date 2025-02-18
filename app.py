from flask import Flask, render_template, jsonify
import os
import json
import logging
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, Filter, FilterExpression
from flask_caching import Cache

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})  # 5 minutes

# Set up logging
logging.basicConfig(level=logging.INFO)

# Validate environment variables
GA4_CREDENTIAL_JSON = os.getenv("GA4_CREDENTIAL_JSON")
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")
if not GA4_CREDENTIAL_JSON or not GA4_PROPERTY_ID:
    logging.error("Missing GA4_CREDENTIAL_JSON or GA4_PROPERTY_ID environment variables!")
    exit(1)

# Initialize Google Analytics Client
def initialize_analytics_reporting():
    try:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(GA4_CREDENTIAL_JSON),
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        return BetaAnalyticsDataClient(credentials=credentials)
    except Exception as e:
        logging.error(f"Failed to initialize GA4 client: {e}")
        raise

# Fetch GA4 data
def fetch_ga4_data(client, property_id, page_path, start_date="7daysAgo", end_date="today"):
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date"), Dimension(name="pagePath"), Dimension(name="browser")],
            metrics=[Metric(name="activeUsers"), Metric(name="screenPageViews"), Metric(name="eventCount")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=FilterExpression(filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(value=page_path)
            ))
        )
        response = client.run_report(request)
        return [
            {
                "date": row.dimension_values[0].value,
                "pagePath": row.dimension_values[1].value,
                "browser": row.dimension_values[2].value,
                "activeUsers": int(row.metric_values[0].value),
                "pageViews": int(row.metric_values[1].value),
                "eventCount": int(row.metric_values[2].value)
            }
            for row in response.rows
        ]
    except Exception as e:
        logging.error(f"Error fetching GA4 data for {page_path}: {e}")
        return []

# Routes
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

@app.route("/ga4-summary-<section>")
@cache.cached(timeout=300)
def ga4_summary_section(section):
    page_paths = {"home": "/", "about": "/about", "faq": "/faq", "live-stats": "/live-stats"}
    if section not in page_paths:
        return jsonify({"error": "Invalid section specified"}), 400
    try:
        client = initialize_analytics_reporting()
        property_id = GA4_PROPERTY_ID
        data = {
            "daily": fetch_ga4_data(client, property_id, page_paths[section], "7daysAgo", "today"),
            "monthly": fetch_ga4_data(client, property_id, page_paths[section], "30daysAgo", "today"),
            "yearly": fetch_ga4_data(client, property_id, page_paths[section], "365daysAgo", "today")
        }
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error in /ga4-summary-{section}: {e}")
        return jsonify({"error": "Failed to fetch GA4 summary data"}), 500

if __name__ == "__main__":
    app.run(debug=True)
