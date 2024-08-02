import os
import pandas as pd
import json
from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from src.data import extract_table_from_pdf, parse_transactions, classify_company, execute_query_and_display
from src.report import generate_bank_statement_report
from dotenv import load_dotenv
import random

load_dotenv()

app = FastAPI()

VALID_TOKEN = os.getenv("SPENDWISE_TOKEN", "your_secret_token")  # Retrieve token from environment variables

df_file_path = 'filtered_data.csv'


class QueryRequest(BaseModel):
    question: str


def verify_token(x_token: str = Header(...)) -> None:
    if x_token != VALID_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
@app.get("/")
def greet_json():
    return {"Spendwise APIs"}

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...), x_token: str = Depends(verify_token)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are accepted.")
    
    pdf_path = f'/tmp/{file.filename}'
    with open(pdf_path, "wb") as buffer:
        buffer.write(await file.read())

    csv_path = extract_table_from_pdf(pdf_path)
    if not csv_path:
        raise HTTPException(status_code=500, detail="Failed to extract tables from the PDF.")

    df = pd.read_csv(csv_path)
    sample_table = df.iloc[:5]['Description'].tolist()
    
    df = parse_transactions(df)
    merchants = df.Merchant.drop_duplicates()
    merchants_str = ', '.join(merchants)
    results = classify_company(merchants_str)
    category_map = json.loads(results)
    df['Category_freetext'] = df['Merchant'].map(category_map)

    categories = ['fitness', 'groceries', 'restaurants and cafes', 'healthcare', 'clothing', 'jewelry',
                  'transportation', 'phone and internet', 'miscellaneous', 'others', 'e-commerce', 'food delivery']

    def find_first_match(text, categories):
        for category in categories:
            if category in text.lower():
                return category
        return None

    df['Merchant'] = df['Merchant'].str.strip().str.lower()
    category_map = {k.lower(): v for k, v in category_map.items()}
    df['Category_freetext'] = df['Merchant'].map(category_map)
    df['Category'] = df['Category_freetext'].apply(lambda x: find_first_match(x, categories))

    cols = df.columns.to_list() + ['Category']
    df_filtered = df[cols]
    df_filtered.to_csv(df_file_path, index=False)

    report_content = generate_bank_statement_report(df,markdown=False)
    return JSONResponse(content={"message": "PDF processed successfully.", "sample_table": sample_table, "report_content": report_content})


@app.post("/ask/")
async def ask_question(request: QueryRequest, x_token: str = Depends(verify_token)):
    messages = [
        "Hang tight, we're working on it!",
        "Hold up, we’re fetching the info you need!",
        "Give us a moment, we’re on it!",
        "One moment please, we’re getting that sorted!",
        "We’re on the case, check back in a bit!",
        "Be patient, magic is happening behind the scenes!",
        "Sit tight, we’re working our magic!",
        "We’re processing your request – please bear with us!"
    ]
    response_message = random.choice(messages)

    if os.path.exists(df_file_path):
        try:
            df = pd.read_csv(df_file_path)
            results = execute_query_and_display(request.question, df,markdown=False)
            return JSONResponse(content={"message": response_message, "response": results})
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error processing the query")
    else:
        raise HTTPException(status_code=404, detail="File not found. Please ensure the file exists and try again.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
