import discord
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
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

                # Extract text from the PDF
                text = extract_text_from_pdf(pdf_path)
                
                # Send the extracted text back to the channel
                if text:
                    await message.channel.send(f'Content of the PDF:\n{text}')
                else:
                    await message.channel.send('Failed to extract content from the PDF.')

def extract_text_from_pdf(pdf_path):
    try:
        document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        print(f'Error extracting text from PDF: {e}')
        return None

# Run the bot
client.run(TOKEN)
