import requests
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
import sys

# API details
#API_KEY = "CNL41TOW59O8GCUD"
#if len(sys.argv) < 2:
#    print("Error: No PDF file path provided.")
#    sys.exit(1)
API_KEY = '1'
BASE_URL = "https://www.alphavantage.co/query"

# MongoDB connection details
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'semi_structured_data'
COLLECTION_NAME = 'Api_data'

# Fetch income statement data
params = {
    "function": "INCOME_STATEMENT",
    "symbol": "IBM",
    "apikey": API_KEY
}

response = requests.get(BASE_URL, params=params)

if response.status_code == 200:
    # Parse the JSON response
    income_data = response.json()
    annual_reports = income_data.get("annualReports", [])

    if not annual_reports:
        print("No annual report data available.")
        exit()

    # Extract cost of revenue and other categories
    cost_of_revenue = annual_reports[0].get("costOfRevenue", 0)
    other_categories = {
        "Gross Profit": annual_reports[0].get("grossProfit", 0),
        "Operating Expenses": annual_reports[0].get("operatingExpense", 0),
        "R&D Expenses": annual_reports[0].get("researchAndDevelopment", 0),
        "SellingGeneralAndAdministrative": annual_reports[0].get("sellingGeneralAndAdministrative", 0),
    }

    classification = {"Cost of Revenue": cost_of_revenue}
    classification.update({key: value for key, value in other_categories.items() if value != 0})

    # Visualize the classification
    df = pd.DataFrame(list(classification.items()), columns=["Category", "Amount"])
    plt.figure(figsize=(8, 8))
    plt.pie(df["Amount"], labels=df["Category"], autopct="%1.1f%%", startangle=140)
    plt.title(f"Cost Breakdown for {annual_reports[0].get('fiscalDateEnding')}")
    plt.show()

    # Insert data into MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Prepare data to insert into MongoDB
    document = {
        "fiscalDateEnding": annual_reports[0].get("fiscalDateEnding"),
        "classification": classification
    }

    collection.insert_one(document)
    print("Classified cost of revenue data inserted into MongoDB successfully!")

else:
    print("Error:", response.status_code, response.text)
