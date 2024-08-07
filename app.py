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
from fastapi.middleware.cors import CORSMiddleware
from apps.run_chain import run_chain
from apps.upload_file import upload_file
from apps.upload_file import generate_sqldb
import openai
from langchain_openai import ChatOpenAI
import os
import uvicorn

#initilise llm
llm = ChatOpenAI(
    model="tiiuae/falcon-180B-chat",
    api_key=os.getenv("AI71_API_KEY"),
    base_url="https://api.ai71.ai/v1/",
    temperature=0,
)

generate_sqldb()

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specify allowed methods
    allow_headers=["X-Custom-Header", "Content-Type"],  # Specify allowed headers
)
VALID_TOKEN = os.getenv("SPENDWISE_TOKEN")  # Retrieve token from environment variables

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
    pdf_path = f'/tmp/bank_statement.pdf'
    with open(pdf_path, "wb") as buffer:
        buffer.write(await file.read())
    upload_file(pdf_path)
    return JSONResponse(content={"message": "PDF processed successfully.", "sample_table": '', "report_content": 'breakdown my expenditure by category'})


@app.post("/ask/")
async def ask_question(request: QueryRequest, x_token: str = Depends(verify_token)):
    results = run_chain(request.question)
    return JSONResponse(content={"message": '', "response": results})


if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
