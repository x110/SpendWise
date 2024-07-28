# SpendWise - AI-Powered Spending Insights Chatbot
## Project Overview
SpendWise is an AI-powered chatbot designed to categorize individual spending from bank statements and provide insightful analytics. Users can interact with SpendWise in natural language to get detailed answers about their monthly expenditures and generate summary reports. Utilizing Falcon language models though AI71 apis, SpendWise automates transaction categorization and offers personalized financial insights.
## Objectives
- Automate Transaction Categorization: Utilize an LLM to accurately categorize each transaction from bank statements into predefined spending categories (e.g., groceries, entertainment, utilities).
- Monthly Spending Summaries: Generate comprehensive summary reports of monthly spending, highlighting key areas of expenditure and trends.
- Natural Language Query Handling: Enable users to interact with SpendWise using natural language to get answers about their spending patterns and specific transactions.
## Benefits
- Time Savings: Automate the tedious process of manual transaction categorization and report generation.
- Financial Awareness: Empower users with detailed insights into their spending habits, promoting better financial management.
- User-Friendly: Enable users to query their spending information in natural language, making it easy and intuitive to use.
## Example Scenario
A user asks SpendWise, "How much did I spend on groceries last month?" The chatbot, utilizing Falcon model, categorizes all relevant transactions, calculates the total spending on groceries, and provides a detailed response. The user can also request a summary report for the entire month, highlighting key spending areas and trends. Queries can be as simple as "Show me my entertainment expenses" or "What was my biggest purchase last month?"


## Milestone: SpendWise Bot Initial Prototype

1. **Integration with Discord Bot**
   - [x] Develop chatbot interface on Discord.

2. **Upload Monthly Bank Statement File to Server through Bot Interface**
    - [x] Implement file upload feature.

3. **Extract Tables from PDF**
   - [x] Use PDF parsing libraries for accurate data extraction.

4. **Data Cleanup and Standardization**
   - [x] Normalize and clean extracted data.

5. **Extract Merchant Name**
   -[x] Identify and extract merchant names from transactions.

6. **Use AI71 APIs to Classify Transactions**
   - Categorize transactions using AI71 APIs 
   - Implement fallback for unrecognized transactions.

7. **Bot Reply with Summary Report**
   - Generate and format summary report of categorized transactions.

8. **Converting natural language to sql queries**

9. **Test and Collect Feedback from Mentors**
   - Conduct testing 
   - Gather and implement feedback from mentors.

## Milestone: SpendWise Bot 2nd Prototype

1. **Dataset Preparation and Testing**
   - Collect and generate datasets to evaluate the SpendWise functionality and performance.

2. **Testing Framework Development**
   - Develop testing scripts to automate the evaluation process.
   - Implement mechanisms to log and analyze test results.

3. **Backend and Frontend Integration**
   - Identify all API endpoints necessary for interaction between the frontend and the backend.
   - Define the data formats and structures for each API endpoint, detailing request and response specifications.
