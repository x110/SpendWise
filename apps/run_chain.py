from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
import openai
import os
import re
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
load_dotenv()

llm=ChatOpenAI( model="tiiuae/falcon-180B-chat",
    api_key= os.getenv("AI71_API_KEY"),
    base_url="https://api.ai71.ai/v1/",
    temperature=0,
    )


def clean_sql_query(query):
    # Find the first semicolon and truncate everything after it
    cleaned_query = re.split(r';\s*', query)[0] + ';'
    return cleaned_query.strip()


def chatbot(user_input):
    try:
        # Initialize the ChatOpenAI
        llm = ChatOpenAI(
            model="tiiuae/falcon-180B-chat",
            api_key=os.getenv("AI71_API_KEY"),
            base_url="https://api.ai71.ai/v1/",
            temperature=0,
        )
        db = SQLDatabase.from_uri("sqlite:///expenses.db")
        # Define the template for the prompt
        template = """
        You are an intelligent MySQL chatbot and your name is SpendWise who will talk about expense history. Help the following question with a brilliant answer. Get the expense data from SQL database named 'expenses'.
        Columns in 'expenses' table:
        CREATE TABLE expenses (
	          "Merchant" TEXT,
	          "Location" TEXT,
	          "Date" TIMESTAMP,
	          "Amount" REAL,
	          "Category_freetext" TEXT,
	          "Category" TEXT
        ) Make SQL query according to question and the different categories are 'fitness', 'groceries', 'restaurants and cafes', 'healthcare', 'clothing', 'jewelry', 'transportation', 'phone and internet', 'miscellaneous', 'others', 'e-commerce', 'food delivery'. You should focus only on 'category' column present in the table for creating the SQL query. Don't choose any other columns to create the SQL query.
        When the question is about summary report/summary of the transactions, provide the total expense corresponding to each category in descending order. When you are asked to calculate total expense, provide the sum total of all categories. When you are asked to comapre different categories, provide the result with all mentioned categories in  the appropriate order. 
        When you are asked to provide expenses related to a certain item, group all the categories this item can fit into. For example, if you are asked to calculate expenses for food , you need to consider categories like 'food delivery','groceries' and 'restaurants and cafes'to provide answer. You are asked to give the exact SQL query in one command only in the answer. You don't need to explain about it.
        Don't append any characters/letters/words/symbols to the SQL command.
        Question:{question}
        Answer:"""

        # Create the prompt template
        prompt = PromptTemplate(template=template, input_variables=['question'])

        # Initialize the LLM chain
        llm_chain = LLMChain(prompt=prompt, llm=llm)

        # Generate the response
        response = llm_chain.invoke(user_input)

        # Ensure it's a string before processing
        if isinstance(response["text"], str):
            # Clean the generated SQL query
            cleaned_sql_query = clean_sql_query(response["text"])

            # Run the SQL query
            if db.run(cleaned_sql_query):
              result = db.run(cleaned_sql_query)
              return result
            else :
              return "No contents to share at the moment"
        else:
            #print("The response does not contain a valid SQL string.")
            return "No contents to share at the moment"

    except Exception as e:
        #print(f"Error: {e}")
        return "No contents to share at the moment"
    

def generate_answer(question, result):
    system_message = SystemMessage(content="You are an expense assistant and your name is SpendWise. Given the following user question and the corresponding SQL result, answer the user question based on the data present in SQL result and ignore what you are not provided with. If The result info appears to be an empty tuple, just say that the user has not made any expense. The currency used is AED. Ignore Total expenses from all categories. If user is asking any other questions, give tricky and intelligent responses")
    human_message = HumanMessage(content=f"""
    Question: {question}
    SQL Result: {result}
    Answer:
    """)

    response = llm.invoke([system_message, human_message])


    return response.content


def run_chain(question):
    # Generate SQL query
    result = chatbot({"question": question})

    # Generate the final answer

    final_answer = generate_answer(question, result)

    return final_answer