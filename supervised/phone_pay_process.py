import pytesseract
from PIL import Image
import os
import re
import sys
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# MongoDB connection details
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'supervised_data'
METADATA_COLLECTION = 'metadata'
TRANSACTIONS_COLLECTION = 'phone_pay_transactions'

# Step 1: Setup MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
metadata_collection = db[METADATA_COLLECTION]
transactions_collection = db[TRANSACTIONS_COLLECTION]

# Step 2: Perform OCR and extract text from images
if len(sys.argv) < 2:
    print("Error: No folder path provided.")
    sys.exit(1)
folder_path = sys.argv[1]

extracted_text = ""
num_files = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
for i in range(1, num_files + 1):
    image_path = os.path.join(folder_path, f"{i}.jpg")
    image = Image.open(image_path)
    extracted_text += pytesseract.image_to_string(image, config='--psm 6', lang='eng') + '\n'

# Step 3: Clean and format the text data
pattern = r"(Received from|Mobile recharged|Paid to|Transfer to)\n(.*)\n(.*)"
matches = re.findall(pattern, extracted_text)
cleaned_text = []
for match in matches:
    cleaned_text.append(f"{match[0]}\n{match[1].strip()}\n{match[2].strip()}\n")

# Step 4: Parse cleaned text into structured format
data_list = []
pattern = r'(Received from|Mobile recharged|Paid to|Transfer to)\n([A-Za-z.\s]+)([\w\d.,]+)\n'
for entry in cleaned_text:
    match = re.search(pattern, entry)
    if match:
        transaction_type, name, amount = match.groups()
        data_list.append([transaction_type.strip(), name.strip(), amount.strip()])

# Step 5: Process the data (Remove invalid rows)
processed_data = []
for row in data_list:
    transaction_type, name, amount = row
    try:
        float(amount.replace(",", ""))  # Check if the amount is numeric
        processed_data.append([transaction_type, name, amount])
    except ValueError:
        continue

# Step 6: Convert processed data to DataFrame
df = pd.DataFrame(processed_data, columns=["Transaction Type", "Name", "Amount"])

# Step 7: Fetch metadata (category rules) from MongoDB
metadata = metadata_collection.find_one({}, {"_id": 0, "category_rules": 1})
if not metadata or "category_rules" not in metadata:
    print("No category rules found in the metadata collection.")
    sys.exit(1)

category_rules = metadata["category_rules"]

# Step 8: Categorize transactions
def categorize_transaction(name):
    for category, keywords in category_rules.items():
        if any(keyword.lower() in name.lower() for keyword in keywords):
            return category
    return "Others"  # Default category if no match is found

df["Category"] = df["Name"].apply(categorize_transaction)

# Step 9: Convert categorized data to a dictionary and insert into MongoDB
categorized_data = df.to_dict(orient='records')
transactions_collection.insert_many(categorized_data)

# Output the results
print(f"Inserted {len(categorized_data)} categorized transactions into MongoDB collection '{TRANSACTIONS_COLLECTION}'.")




# Assuming you have the 'df' DataFrame with the 'Category' and 'Amount' columns

# Group data by category and sum the amounts
category_sums = df.groupby('Category')['Amount'].sum()

# Create the pie chart
plt.figure(figsize=(8, 6))
plt.pie(category_sums, labels=category_sums.index, autopct='%1.1f%%', startangle=140)
plt.title('Transaction Categories')
plt.show()