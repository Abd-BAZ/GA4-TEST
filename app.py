from flask import Flask, render_template, jsonify
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange

app = Flask(__name__)

# Function to initialize Google Analytics Data API client
def initialize_analytics_reporting():
    # Define the path to your service account credentials file
    credentials_path = "credentials/ga-4-website-448507-3efe2dc5a106.json"
    
    # Define the required scopes for accessing the Google Analytics API
    SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']

    # Authenticate and create a client using the service account
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES)
    
    # Initialize the Analytics Data API client
    client = BetaAnalyticsDataClient(credentials=credentials)
    
    return client

# Function to fetch GA-4 data (example: users by date)
def fetch_ga4_data(client):
    property_id = '473956527'  

    # Set up the query request (example: users by date)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[{'name': 'date'}],
        metrics=[{'name': 'activeUsers'}],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")]  # Specify the date range
    )

    # Run the query
    response = client.run_report(request)

    # Process the response data
    report_data = []
    for row in response.rows:
        data = {
            "date": row.dimension_values[0].value,
            "activeUsers": row.metric_values[0].value
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
