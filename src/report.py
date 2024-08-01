import pandas as pd

def generate_bank_statement_report(df):
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')

    # Analytics
    total_expenditure = df['Amount'].sum()
    category_summary = df.groupby('Category')['Amount'].sum().reset_index().sort_values(by='Amount', ascending=False)
    merchant_summary = df.groupby('Merchant')['Amount'].sum().reset_index().sort_values(by='Amount', ascending=False).head()
    monthly_summary = df.groupby('Month')['Amount'].sum().reset_index()
    
    # Generating Markdown report 
    markdown_report = f"""
    # Bank Statement Summary Report
    ## Overview
    - **Total Expenditure:** AED {total_expenditure:.2f}
    """
    markdown_report += "\n## Expenditure by Category\n"
    
    for _, row in category_summary.iterrows():
        category = row['Category']
        amount = row['Amount']
        markdown_report += f"- **{category.capitalize()}:** AED {amount:.2f}\n"

    markdown_report += "\n## Expenditure by Merchant (Top 5)\n"
    
    for _, row in merchant_summary.iterrows():
        merchant = row['Merchant']
        amount = row['Amount']
        markdown_report += f"- **{merchant.capitalize()}:** AED {amount:.2f}\n"
    
    return markdown_report
