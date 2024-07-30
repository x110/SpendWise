import os
import pdfplumber
import pandas as pd
import logging
import json
import requests
import re

def extract_table_from_pdf(pdf_path):
    """
    Extract tables from a PDF file and save them as a CSV file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The path to the saved CSV file.
    """
    try:
        # Extract the base name of the file (without extension)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        # Get the directory path of the PDF file
        directory = os.path.dirname(pdf_path)

        # Create the full CSV file path
        csv_file_path = os.path.join(directory, f"{base_name}.csv")

        # Open the PDF file
        with pdfplumber.open(pdf_path) as pdf:
            all_tables = []
            # Iterate through the pages
            for page in pdf.pages:
                # Extract tables from the page
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)

        if not all_tables:
            logging.warning(f"No tables found in the PDF file: {pdf_path}")
            return ""

        # Combine all tables into a single DataFrame
        df_list = [pd.DataFrame(table[1:], columns=table[0]) for table in all_tables if table]

        # Concatenate all DataFrames
        final_df = pd.concat(df_list, ignore_index=True)

        # Save the final DataFrame to a CSV file
        final_df.to_csv(csv_file_path, index=False)

        logging.info(f"Tables extracted and saved to '{csv_file_path}'.")

        return csv_file_path

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return ""

# Example usage:
#if __name__ == "__main__":
#    logging.basicConfig(level=logging.INFO)
#    pdf_path = "./data/transactions_july_2024.pdf"
#    extract_table_from_pdf(pdf_path)


# Function to process the DataFrame and parse transactions
def process_transactions(data_path):
    # Load the data
    df = pd.read_csv(data_path)
    df = df.rename(columns={'Date':'Date0'})
    
    # Drop rows where all elements are NaN
    df = df.dropna(how='all')
    
    # Replace newline characters in 'Description' column
    df['Description'] = df['Description'].str.replace('\n', ' ')
    
    # List of UAE cities
    uae_cities = ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Ras Al Khaimah', 'Fujairah', 'Umm Al Quwain', 'Al Ain']
    
    # Function to extract city name from a string
    def extract_city_name(name):
        for city in uae_cities:
            if city.lower() in name.lower():
                return city
        return ''
    
    # Function to replace a substring in a string, ignoring case
    def replace_ignore_case(original_str, old_substr, new_substr):
        pattern = re.compile(re.escape(old_substr), re.IGNORECASE)
        return pattern.sub(new_substr, original_str)
    
    # Regex patterns for parsing transactions
    pattern_card = re.compile(
        r'CARD NO\.(\d+\*{8}\d{4}) (.+):([A-Z]{2}) (\d+) (\d{2}-\d{2}-\d{4}) ([\d\.]+),([A-Z]+)'
    )
    
    pattern_ipi = re.compile(
        r'IPI TT REF: (\w+) ([^\d\s]+ [^\d\s]+ [^\d\s]+) (.+)$'
    )
    
    # Function to parse a transaction description
    def parse_transaction(transaction):
        card_match = pattern_card.search(transaction)
        ipi_match = pattern_ipi.search(transaction)
        
        if card_match:
            merchant_and_city = card_match.group(2).strip()
            city = extract_city_name(merchant_and_city)
            merchant = replace_ignore_case(merchant_and_city, city, "")
            
            return {
                "Card Number": card_match.group(1),
                "Merchant": merchant,
                "Location": city,
                "Country Code": card_match.group(3).strip(),
                "Transaction ID": card_match.group(4),
                "Date": card_match.group(5),
                "Amount": card_match.group(6),
                "Currency": card_match.group(7)
            }
        elif ipi_match:
            reference = ipi_match.group(1)
            details = ipi_match.group(2)
            return {
                'Card Number': None,
                'Merchant': None,
                "Location": None,
                "Country Code": None,
                "Transaction ID": None,
                'Date': None,
                'Amount': None,
                'Currency': None,
                'Reference': reference,
                'Details': details
            }
        else:
            return {
                'Card Number': None,
                'Merchant': None,
                "Location": None,
                "Country Code": None,
                "Transaction ID": None,
                'Date': None,
                'Amount': None,
                'Currency': None,
                'Reference': None,
                'Details': None
            }
    
    # Apply parsing function to each row in the DataFrame
    df_parsed = df['Description'].apply(parse_transaction).apply(pd.Series)
    
    # Combine parsed information with the original DataFrame
    df_final = pd.concat([df, df_parsed], axis=1)
    
    return df_final

# Example usage:
# df_final = process_transactions('path_to_your_file.csv')
# print(df_final)

import time

def fetch_with_retry(url: str, headers: dict, payload: dict, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=payload)
            
            if response.status_code == 429:  # Rate limit exceeded
                retry_after = response.headers.get("Retry-After")
                if retry_after is None:
                    retry_after = response.json().get("retry_after", 1)  # Fallback to 1 second if not provided
                retry_after = int(retry_after)
                
                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                # Successful response or other status code
                response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx and 5xx)
                return response.json()
        
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            time.sleep(1)  # Short sleep before retrying in case of connection errors or timeouts

    raise Exception("Max retries exceeded")

def classify_company(user_content):
    url = "https://api.ai71.ai/v1/chat/completions"
    AI71_TOKEN = os.getenv('AI71_TOKEN')

    categories = [
    'fitness',
    'groceries',
    'restaurants and cafes',
    'healthcare', 
    'clothing',
    'jewelry',
    'transportation',
    'phone and internet', 
    'miscellaneous',
    'others',
    'e-commerce',
    'food delivery'
    ]

    categories_str = ', '.join(categories)

    role_content = (
        f"You will be provided with company names, and your task is to classify them to one of the following "
        f"{categories_str}"
        f" return them formated as json where field is company name and value is category"
    )
    
    payload = json.dumps({
        "model": "tiiuae/falcon-180b-chat",
        "messages": [
            {
                "role": "system",
                "content": role_content
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
    })
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {AI71_TOKEN}'
    }
    
    #response = requests.post(url, headers=headers, data=payload)
    response = fetch_with_retry(url, headers, payload)

    try:
        response_json = response.json()
        choices = response_json.get('choices', [])
        if choices:
            result = choices[0].get('message', {}).get('content', '').strip()
            return result
        else:
            return None
            
    except ValueError:
        return None
