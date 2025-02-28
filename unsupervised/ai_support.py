import sys
from pymongo import MongoClient
import google.generativeai as genai

# Configure API key from environment variable for security
genai.configure(api_key="")

# Function to fetch and clean data from MongoDB
def extract_clean_data():
    try:
        client = MongoClient("mongodb://localhost:27017/")

        

        collection = client["unsupervised_data"]["Training_data"]
        data = list(collection.find())

        # Check if data exists
        if not data:
            print("No data found.")
            return None

        # Clean data (remove _id and replace newlines with spaces)
        return [
            {key: str(value).replace("\n", " ") for key, value in doc.items() if key != "_id"}
            for doc in data
        ]
    except Exception as e:
        print(f"Error fetching or cleaning data: {e}")
        return None

# Function to generate a response from Gemini API
def chat_with_gemini(user_input, context_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(contents=[{"text": "read the below\n" + context_text + "\n Respond for -> " + user_input}])
    return response.text

# Main flow
if __name__ == "__main__":
    # Get the user prompt from command-line arguments
    if len(sys.argv) < 2:
        print("Error: No prompt provided. Please pass a prompt as a command-line argument.")
        sys.exit(1)

    user_input = sys.argv[1]  # First argument after the script name

    # Extract and clean data from MongoDB
    data = extract_clean_data()
    if data:
        # Convert cleaned data to a single string (no file saving)
        context_text = ",".join([str(item) for doc in data for item in doc.values()])

        # Generate a response from the Gemini API
        gemini_response = chat_with_gemini(user_input, context_text)
        print( gemini_response)
