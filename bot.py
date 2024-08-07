import discord
import os
import pdfplumber
import pandas as pd
import json
from src.data import extract_table_from_pdf, parse_transactions, classify_company, execute_query_and_display, format_table_as_text
from src.report import generate_bank_statement_report
from dotenv import load_dotenv
import random
load_dotenv()

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

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

    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith('.pdf'):
                await message.channel.send('"PDF received! Extracting content now...')
                pdf_path = "./data/bank_statement.pdf"
                await attachment.save(pdf_path)

                csv_path = extract_table_from_pdf(pdf_path)
                if csv_path:
                    await message.channel.send('Successfully extracted the content of the PDF.')
                else:
                    await message.channel.send('Failed to extract tables from the PDF.')
                
                df = pd.read_csv(csv_path)
                table_str = df[['Description']].head().to_markdown(index=False) #TODO check if column name exists
                await message.channel.send('\nHere is a sample of the transactions:\n')
                await message.channel.send(f'```\n{table_str}\n```')

                await message.channel.send('Identifying key details from transactions...\n')
                df = parse_transactions(df)
                table_str = df.head().to_markdown(index=False)
                await message.channel.send(f'```\n{table_str}\n```')
                
                await message.channel.send('Hang tight! We are categorizing your transaction into the right spending category. This will just take a moment.\n')
                cols = df.columns.to_list()
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

                df_filtered = df[cols]
                df_filtered.to_csv(df_file_path, index=False)

                await message.channel.send('Creating your Bank Statement Analytics Report...\n')
                md_report = generate_bank_statement_report(df)
                await message.channel.send(md_report)
                await message.channel.send("-# To run queries on the data, type /ask followed by your question. E.g., '/ask What is my biggest purchase?'")
    
                
    if message.content.startswith('/ask'):
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
        await message.channel.send(response_message)
        if os.path.exists(df_file_path):
            try:
                df = pd.read_csv(df_file_path)
                markdown_content = execute_query_and_display(message.content, df)
                await message.channel.send(markdown_content)
            except Exception as e:
                await message.channel.send(f'Error processing the query')
        else:
            await message.channel.send('File not found. Please ensure the file exists and try again.')
        






# Run the bot
client.run(TOKEN)
