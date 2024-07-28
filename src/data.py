import os
import pdfplumber
import pandas as pd
import logging

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
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pdf_path = "./data/transactions_july_2024.pdf"
    extract_table_from_pdf(pdf_path)
