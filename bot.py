import discord
import os
import pdfplumber
import pandas as pd
import json
from src.data import extract_table_from_pdf, process_transactions, classify_company, execute_query_and_display
from dotenv import load_dotenv
load_dotenv()

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = os.getenv('DISCORD_BOT_TOKEN_DEV')

# Create a new instance of the bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    df_file_path = 'filtered_data.csv'
    # Check if the message contains an attachment
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith('.pdf'):
                await message.channel.send('PDF received! Extracting content...')

                # Download the PDF file
                pdf_path = f'/tmp/{attachment.filename}'
                await attachment.save(pdf_path)

                # Extract Tables from the PDF
                csv_path = extract_table_from_pdf(pdf_path)
                if csv_path:
                    await message.channel.send('Successfully extracted the content of the PDF.')
                else:
                    await message.channel.send('Failed to extract tables from the PDF.')
                df = process_transactions(csv_path)
                df['Date'] = pd.to_datetime(df['Date'])#, errors='coerce')

                # Convert other potentially numeric columns that were inferred as 'object'
                #df['Debits'] = pd.to_numeric(df['Debits'])#, errors='coerce')
                #df['Credits'] = pd.to_numeric(df['Credits'])#, errors='coerce')
                #df['Balance'] = pd.to_numeric(df['Balance'])#, errors='coerce')
                df['Amount'] = pd.to_numeric(df['Amount'])#, errors='coerce')

                # Handle missing values if necessary
                df.fillna({
                    'Debits': 0,
                    'Credits': 0,
                    'Balance': 0,
                    'Amount': 0
                }, inplace=True)

                #df = df.dropna(how='all')
                #df = df.dropna(subset=['Merchant'])
                table_str = df[['Description']].head().to_markdown(index=False)  # Use markdown for better formatting
                await message.channel.send(f'```\n{table_str}\n```')
                
                cols = ['Merchant','Location','Date', 'Amount']
                table_str = df.filter(cols).head().to_markdown(index=False)  # Use markdown for better formatting
                await message.channel.send(f'```\n{table_str}\n```')
                
                merchants = df.Merchant.drop_duplicates()
                merchants_str = ', '.join(merchants)
                results = classify_company(merchants_str)
                category_map = json.loads(results)
                df['Category_freetext'] = df['Merchant'].map(category_map)#TODO cache
                categories = ['fitness', 'groceries', 'restaurants and cafes', 'healthcare', 'clothing', 'jewelry',
                              'transportation', 'phone and internet', 'miscellaneous', 'others', 'e-commerce', 'food delivery']

                def find_first_match(text, categories ):
                    for category in categories :
                        if category in text.lower():
                            return category
                    return None
                # Strip leading/trailing spaces and convert to lowercase
                df['Merchant'] = df['Merchant'].str.strip().str.lower()

                # Update category_map to match the cleaned Merchant values if needed
                category_map = {k.lower(): v for k, v in category_map.items()}

                # Apply the mapping again
                df['Category_freetext'] = df['Merchant'].map(category_map)

                df['Category'] = df['Category_freetext'].apply(lambda x: find_first_match(x, categories))
                cols += ['Category']
                table_str = df.filter(cols).head().to_markdown(index=False)  # Use markdown for better formatting
                await message.channel.send(f'```\n{table_str}\n```')
                # Convert 'Date' column to datetime format
                df['Date'] = pd.to_datetime(df['Date'])

                # Monthly spending summary
                df['Month'] = df['Date'].dt.to_period('M')

                columns_to_save = ['Date','Amount','Category','Merchant']
                df_filtered = df[columns_to_save]
                file_path = 'filtered_data.csv'
                df_filtered.to_csv(df_file_path, index=False)

                monthly_summary = df.groupby('Month')['Amount'].sum().reset_index()

                # Top spenders by merchant
                merchant_summary = df.groupby('Merchant')['Amount'].sum().reset_index().sort_values(by='Amount', ascending=False)

                # Category spending distribution
                category_summary = df.groupby('Category')['Amount'].sum().reset_index()

                # Calculate overall total spending
                total_spending = df['Amount'].sum()

                # Summary report
                dfs = [monthly_summary,merchant_summary, category_summary]

                markdown_content = "Summary Report:\n"
                markdown_content += f"Total Spending: {total_spending}\n\n"

                for i, df in enumerate(dfs, start=1):
                    markdown_table = df.to_markdown()
                    markdown_content += markdown_table
                    markdown_content += "\n\n"  # Add some spacing between tables
                
                await message.channel.send(f'```\n{markdown_content}\n```')
    if message.content.startswith('/ask'):
        if os.path.exists(df_file_path):
            try:
                df = pd.read_csv(df_file_path)
                markdown_content = execute_query_and_display(message.content, df)
                await message.channel.send(f'```\n{markdown_content}\n```')
            except Exception as e:
                await message.channel.send(f'Error processing the file: {e}')
        else:
            await message.channel.send('File not found. Please ensure the file exists and try again.')
        






# Run the bot
client.run(TOKEN)
