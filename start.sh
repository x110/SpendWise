#!/bin/bash

# Start the Discord bot in the background
python bot.py &

# Capture the PID of the bot process if you need to manage it later
BOT_PID=$!

# Start the Uvicorn server
uvicorn app:app --host 0.0.0.0 --port 7860

# Optionally wait for the bot process to finish
wait $BOT_PID
