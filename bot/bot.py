import discord
import os
import pdfplumber
import pandas as pd
from dotenv import load_dotenv
import json
from data import extract_table_from_pdf, process_transactions, classify_company


load_dotenv()

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = os.getenv('DISCORD_BOT_DEV_TOKEN')

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
                df = process_transactions(csv_path)
                



                
                if csv_path:
                    await message.channel.send('Successfully extracted the content of the PDF.')
                else:
                    await message.channel.send('Failed to extract tables from the PDF.')

                await message.channel.send(df.head().to_json(orient='records'))

# Run the bot
client.run(TOKEN)
