import os

import slack
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter


# run local tunnel first
# https://slackbotforsofaa2023.loca.lt

load_dotenv()
SLACK_TOKEN = os.environ['SLACK_TOKEN']
SIGNING_SECRET = os.environ['SIGNING_SECRET']

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)

client = slack.WebClient(token=SLACK_TOKEN)

client.chat_postMessage(channel='#dev', text="Hello world!")

if __name__ == '__main__':
    app.run(debug=True, port=5023)
