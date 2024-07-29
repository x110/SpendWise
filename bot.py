import discord
import os
import pdfplumber
import pandas as pd
import json
from src.data import extract_table_from_pdf, process_transactions, classify_company


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
                
                table_str = df[['Description']].head().to_markdown(index=False)  # Use markdown for better formatting
                await message.channel.send(f'```\n{table_str}\n```')
                df = process_transactions(csv_path)
                cols = ['Card Number','Merchant','Location','Date', 'Amount']
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

                df['Category'] = df['Category_freetext'].apply(lambda x: find_first_match(x, categories))
                cols += ['Category']
                table_str = df.filter(cols).head().to_markdown(index=False)  # Use markdown for better formatting
                await message.channel.send(f'```\n{table_str}\n```')






# Run the bot
client.run(TOKEN)
