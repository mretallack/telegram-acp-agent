import sys
import logging
import json
import time
sys.path.append("/home/mark/git/telegram-goose-bot")

logging.basicConfig(level=logging.INFO)

from acp_client import ACPClient

client = ACPClient("/home/mark/git/telegram-goose-bot")
try:
    client.start()
    client.initialize()
    session_id = client.create_session("/home/mark/git/telegram-goose-bot")
    
    print("\nSENDING STATUS SLASH COMMAND AS PROMPT...")
    prompt = [{"type": "text", "text": "/status"}]
    res = client.send_prompt(session_id, prompt)
    print("PROMPT RESPONSE:")
    print(json.dumps(res, indent=2))
    
    time.sleep(1)
finally:
    client.close()
