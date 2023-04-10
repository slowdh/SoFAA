import os

import slack
from dotenv import load_dotenv


load_dotenv()

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

client.chat_postMessage(channel='#dev', text="Hello world!")
