import os
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import pandas as pd
from pymongo import MongoClient
import sys

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017/')
db = client['supervised_data']
collection = db['bank_transactions']

import os
import shutil

def convert_pdf_to_images(pdf_path, output_folder, dpi=300):
    """
    Converts PDF pages into images and saves them in the specified folder.
    """
    # Clear the output folder if it exists
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)  # Delete the folder and its contents
    os.makedirs(output_folder)  # Recreate the folder

    doc = fitz.open(pdf_path)
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
        image_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
        pix.save(image_path)

    return output_folder


def extract_text_from_images(image_folder):
    """
    Extracts text from all images in the specified folder.
    """
    extracted_text = ""
    for image_file in sorted(os.listdir(image_folder)):
        if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_folder, image_file)
            with Image.open(image_path) as image:  # Use 'with' to auto-close the image
                text = pytesseract.image_to_string(image, config='--psm 6', lang='eng')
                extracted_text += text + "\n"

    return extracted_text


def clean_text(raw_text):
    """
    Cleans and normalizes extracted text by removing unwanted characters.
    """
    # Normalize spaces and remove special characters
    cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()
    cleaned_text = re.sub(r'[$!(){}#]', '', cleaned_text)
    return cleaned_text


def extract_transaction_data(cleaned_text):
    """
    Extracts relevant transaction details using regex.
    """
    # Define regex for transaction details
    pattern = r'(\d{2} [A-Za-z]{3} \d{4}) TRANSFER \w+ (\d{10,16}) - (\d{1,5}\.\d{2}) \d{1,5}\.\d{2} UPI/(\w+)/\d{12}/([\w\s]+)/([\w\s]+)/([\w.-]+)/(\w+)'
    
    transactions = []
    matches = re.finditer(pattern, cleaned_text)
    for match in matches:
        transaction = {
            "date": match.group(1),
            "transfer_details": f"TRANSFER TO {match.group(2)}, {match.group(7)}",
            "amount": match.group(3),
            "debited_or_credited": match.group(4),
            "name": match.group(5).strip(),
            "bank": match.group(6),
            "description": match.group(8)
        }
        transactions.append(transaction)

    return transactions


def save_to_mongodb(transactions):
    """
    Saves extracted transaction data into MongoDB.
    """
    if transactions:
        collection.insert_many(transactions)
        print(f"Inserted {len(transactions)} transactions into MongoDB.")
    else:
        print("No transactions to save.")


def main():
    # Input paths
    if len(sys.argv) < 2:
        print("Error: No PDF file path provided.")
        sys.exit(1)
    pdf_path = sys.argv[1]
    output_folder = r"C:\python projects\springboard\ocr_of_bankstatements\output_images"

    convert_pdf_to_images(pdf_path, output_folder)

    raw_text = extract_text_from_images(output_folder)

    cleaned_text = clean_text(raw_text)

    transactions = extract_transaction_data(cleaned_text)

    print("Saving data to MongoDB...")
    save_to_mongodb(transactions)

    print("Process complete!")


if __name__ == "__main__":
    main()
