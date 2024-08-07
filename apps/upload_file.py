import requests
import json
import pandas as pd
from dotenv import load_dotenv
import os
import sqlite3
import shutil
import pandas as pd
import os
import json
import requests
import os
import pdfplumber
import logging
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
import re
from langchain_community.utilities import SQLDatabase

#function to extract table from pdf

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
    
# function to parse the transactions

def parse_transactions(df):
    # Load the data
    
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
    df_final['Date'] = pd.to_datetime(df_final['Date'],dayfirst=True)
    df_final['Amount'] = pd.to_numeric(df_final['Amount'])
    df_final.fillna({
        'Debits': 0,
        'Credits': 0,
        'Balance': 0,
        'Amount': 0
        }, inplace=True)

    df_final = df_final.dropna(how='all')
    df_final = df_final.dropna(subset=['Merchant'])
    cols = ['Merchant','Location','Date', 'Amount']
    df_final = df_final.filter(cols)

    return df_final

def find_first_match(text, categories):
        for category in categories:
            if category in text.lower():
                return category
        return None

#function to categorise transactions

def classify_company(user_content):
    url = "https://api.ai71.ai/v1/chat/completions"
    AI71_TOKEN = os.getenv("AI71_API_KEY")

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

    response = requests.post(url, headers=headers, data=payload)

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
    
# function to process pdf file and store it in a SQL database
def generate_sqldb():
    extract_table_from_pdf('data/bank_statement.pdf')

    df =pd.read_csv('data/bank_statement.csv')

    df = parse_transactions(df)


    merchants = df.Merchant.drop_duplicates()
    merchants_str = ', '.join(merchants)
    results = classify_company(merchants_str)
    category_map = json.loads(results)
    df['Category_freetext'] = df['Merchant'].map(category_map)

    categories = ['fitness', 'groceries', 'restaurants and cafes', 'healthcare', 'clothing', 'jewelry',
                  'transportation', 'phone and internet', 'miscellaneous', 'others', 'e-commerce', 'food delivery']

    

    df['Merchant'] = df['Merchant'].str.strip().str.lower()
    category_map = {k.lower(): v for k, v in category_map.items()}
    df['Category_freetext'] = df['Merchant'].map(category_map)
    df['Category'] = df['Category_freetext'].apply(lambda x: find_first_match(x, categories))

    cols = df.columns.to_list() + ['Category']

# Create a connection to an SQLite database (or create one if it doesn't exist)
    conn = sqlite3.connect('expenses.db')

# Write the DataFrame to a SQL table named 'expenses'
    df.to_sql('expenses', conn, if_exists='replace', index=False)

# Commit the changes and close the connection
    conn.commit()
    conn.close()
    db = SQLDatabase.from_uri("sqlite:///expenses.db")
    #print(db.run('SELECT * FROM expenses ORDER BY Amount DESC LIMIT 1'))




#function to handle upload
def upload_file(file):

    save_dir = "./data"
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    shutil.copy(file,save_dir)
    generate_sqldb()




