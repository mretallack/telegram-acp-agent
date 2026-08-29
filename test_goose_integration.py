import sys
import logging
import json
import time
sys.path.append("/home/mark/git/telegram-goose-bot")

logging.basicConfig(level=logging.INFO)

from goose_session_acp import GooseSessionACP

print("Initializing GooseSessionACP...")
session_manager = GooseSessionACP()

# Set current chat ID for sync updates
session_manager.set_chat_id(123456789)

# Define mock send function
def mock_send(chat_id, text, **kwargs):
    print(f"\n[TELEGRAM SEND to {chat_id}]: {text}\n")

session_manager.send_to_telegram = mock_send

print("\nStarting session...")
session_manager.start_session("goose_default")

# Wait a little bit for start-up and initialization to complete
time.sleep(5)

print("\nSending prompt message...")
session_manager.send_message("What is 1+1? Answer in one word.", 123456789)

# Let prompt execute and stream chunks
time.sleep(5)

print("\nClosing sessions...")
session_manager.close()
print("Done!")
