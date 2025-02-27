import streamlit as st
import subprocess
import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient

# Initialize session state variables
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "processed" not in st.session_state:
    st.session_state.processed = False

# Initialize session state for page navigation
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

# Function to navigate between pages
def navigate_to(page):
    st.session_state["page"] = page

# Home page function
def home_page():
    st.title("Expense Tracker")
    st.header("Make Your Choice")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("From Files")
        if st.button("Go to Files", key="go_to_files"):
            navigate_to("Files")

    with col2:
        st.subheader("From Websites")
        if st.button("Go to Websites", key="go_to_websites"):
            navigate_to("Websites")
    
    with col3:
        st.subheader("From AI")
        if st.button("Go to AI support", key ="Go_to_AI_support"):
            navigate_to("Ai")

# Files page function
def files_page():
    st.title("Extract Text from Files")
    st.write("Choose the file type to extract text.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Bank Statements, Invoices (PDF)")
        if st.button("Click Here", key="click_here_pdf"):
            navigate_to("pdf_files")

    with col2:
        st.subheader("Payslips, PhonePe Screenshots (Images)")
        if st.button("Click Here", key="click_here_images"):
            navigate_to("image_files")
        
    if st.button("Back to Home", key="back_to_home_pdf_result"):
        navigate_to("Home")


def pdf_files_page():
    st.subheader("Upload PDF Files (Bank Statements, Invoices)")
    pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if pdf_file:
        # Ensure temp directory exists
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)

        # Save uploaded file
        pdf_path = os.path.join(temp_dir, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        st.success(f"File uploaded: {pdf_file.name}")

        # Store the path in session state
        st.session_state.pdf_path = pdf_path
        st.session_state.processed = False  # Reset processing flag

        if st.button("Proceed", key="proceed_pdf"):
            navigate_to("Pdf_Result")

    if st.button("Back to Files", key="back_to_files_pdf"):
        navigate_to("Files")

    if st.button("Back to Home", key="back_to_home_pdf_result"):
        navigate_to("Home")

# Image files page function
def image_files_page():
    st.subheader("Upload Image Files (JPG, PNG, JPEG)")

    # Multiple file uploader for image files
    multiple_images = st.file_uploader(
        "Upload multiple image files",
        type=["jpg", "png", "jpeg"],
        accept_multiple_files=True,
        key="multiple_images_upload",
    )

    if multiple_images:
        # Ensure temp directory exists
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)

        st.write(f"Uploaded {len(multiple_images)} image file(s).")

        # Save the uploaded images with sequential names
        for idx, image_file in enumerate(multiple_images, start=1):
            image_path = os.path.join(temp_dir, f"{idx}.jpg")  # Save as 1.jpg, 2.jpg, etc.
            with open(image_path, "wb") as f:
                f.write(image_file.read())
            st.success(f"File saved as: {idx}.jpg")

        # Store the folder path in session state for further processing
        st.session_state["temp_dir"] = temp_dir

        st.success(f"All files saved to folder: {temp_dir}")

        if st.button("Proceed to Results", key="proceed_images"):
            navigate_to("Image_Result")

    if st.button("Back to Files", key="back_to_files_images"):
        navigate_to("Files")


def pdf_result_page():
    st.title("PDF Processing Result")
    if st.session_state.pdf_path:
        st.write(f"Processing the PDF file: {st.session_state.pdf_path}")

        if not st.session_state.processed:  # Process only if not already done
            try:
                st.write("Processing PDF...")
                result = subprocess.run(
                    ["python", r"C:\python projects\springboard\BFSI_ocr\supervised\bank_statement.py", 
                     st.session_state.pdf_path],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                st.session_state.processed = True  # Mark as processed
                st.success("PDF processed successfully!")
                st.text("Process Output:")
                st.code(result.stdout)

            except subprocess.CalledProcessError as e:
                st.error(f"Error processing the PDF: {e}")
                st.text("Error Details:")
                st.code(e.stderr)
            except Exception as e:
                st.error(f"Unexpected error: {e}")


    # Handle Back to Files button
    if st.button("Back to Files", key="back_to_files_pdf_result"):
        # Reset processing state and navigate
        st.session_state.processed = False
        st.session_state.pdf_path = None
        navigate_to("Files")

    # Handle Back to Home button
    if st.button("Back to Home", key="back_to_home_pdf_result"):
        st.session_state.processed = False
        st.session_state.pdf_path = None
        navigate_to("Home")



# Image result page function
def image_result_page():
    st.title("Image Processing Result")

    if "temp_dir" in st.session_state:
        temp_dir = st.session_state["temp_dir"]
        st.write(f"Processing the images in folder: {temp_dir}")

        try:
            st.write("Processing images...")
            result = subprocess.run(
                ["python", r"C:\python projects\springboard\BFSI_ocr\supervised\phone_pay_process.py", temp_dir],
                capture_output=True,
                text=True,
                check=True,
            )
            st.success("Images processed successfully!")
            st.text(result.stdout)
        except subprocess.CalledProcessError as e:
            st.error(f"Error processing the images: {e}")
            st.text(e.stderr)
        except Exception as e:
            st.error(f"Unexpected error: {e}")
    if "temp_dir" in st.session_state:
        temp_dir = st.session_state["temp_dir"]

        st.write("Attempting to visualize categorized transaction data...")

        # Connect to MongoDB and fetch data
        MONGO_URI = 'mongodb://localhost:27017/'
        DB_NAME = 'supervised_data'
        TRANSACTIONS_COLLECTION = 'phone_pay_transactions'

        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        transactions_collection = db[TRANSACTIONS_COLLECTION]

        # Fetch data as a DataFrame
        data = list(transactions_collection.find({}, {"_id": 0}))
        if data:
            df = pd.DataFrame(data)
            st.write("### Transactions Summary", df.head())

            # Group by category and sum amounts
            df["Amount"] = df["Amount"].replace(",", "", regex=True).astype(float)
            category_sums = df.groupby("Category")["Amount"].sum()

            # Create the pie chart
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(
                category_sums,
                labels=category_sums.index,
                autopct="%1.1f%%",
                startangle=140,
            )
            ax.set_title("Transaction Categories")
            st.pyplot(fig)
        else:
            st.error("No transaction data found in MongoDB.")

    if st.button("Back to Files", key="back_to_files_image_result"):
        navigate_to("Files")
    if st.button("Back to Home", key="back_to_home_image_result"):
        navigate_to("Home")

# Websites page function
def websites_page():
    st.title("Extract Data from Websites")
    st.write("Enter the API key to fetch data.")

    # Input for API key
    API_KEY = st.text_input("Enter the Alpha Vantage API key:", key="api_key_input")

    if st.button("Fetch and Process Data"):
        if not API_KEY:
            st.error("Please provide a valid API key.")
            return

        BASE_URL = "https://www.alphavantage.co/query"
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
                st.error("No annual report data available.")
                return

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
            st.write("### Cost Breakdown")
            df = pd.DataFrame(list(classification.items()), columns=["Category", "Amount"])
            
            # Create a pie chart using Matplotlib
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(
                df["Amount"],
                labels=df["Category"],
                autopct="%1.1f%%",
                startangle=140
            )
            ax.set_title(f"Cost Breakdown for {annual_reports[0].get('fiscalDateEnding')}")

            # Display the plot in Streamlit
            st.pyplot(fig)

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
            st.success("Classified cost of revenue data inserted into MongoDB successfully!")

        else:
            st.error(f"Error fetching data: {response.status_code}")
            st.text(response.text)

    if st.button("Back ", key="back_to_home_image_result"):
        navigate_to("Home")


def ai_support_page():
    st.title("AI Support")

    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Input box for user prompt
    st.write("Enter your prompt and click the button to execute the Python file.")
    prompt = st.text_input("Enter your prompt:", key="ai_prompt")

    # Ensure that the prompt is provided before running the Python file
    if st.button("Run AI", key="run_ai"):
        if not prompt.strip():
            st.error("Please enter a valid prompt.")
        else:
            try:
                st.write("Running the AI process...")

                # Pass the prompt to the Python file as a subprocess
                result = subprocess.run(
                    ["python", r"C:\python projects\springboard\BFSI_ocr\unsupervised\ai_support.py", prompt ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Add the user input and AI response to the chat history
                st.session_state.chat_history.append({"user": prompt, "ai": result.stdout.strip()})
                st.success("AI script executed successfully!")
            except subprocess.CalledProcessError as e:
                st.error(f"Error running the AI script: {e}")
                st.text(e.stderr)
            except Exception as e:
                st.error(f"Unexpected error: {e}")

    # Display the chat history
    st.write("### Chat History")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        st.markdown(f"**AI:** {chat['ai']}")

    # Back to home button
    if st.button("Back to Home", key="back_to_home_ai_support"):
        navigate_to("Home")



# Render the current page
page = st.session_state["page"]

if page == "Home":
    home_page()
elif page == "Files":
    files_page()
elif page == "pdf_files":
    pdf_files_page()
elif page == "image_files":
    image_files_page()
elif page == "Pdf_Result":
    pdf_result_page()
elif page == "Image_Result":
    image_result_page()
elif page == "Websites":
    websites_page()
elif page == "Ai":  # Add AI support page navigation
    ai_support_page()
