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
BOT_ID = client.api_call("auth.test")['user_id']

@slack_event_adapter.on('message')
def handle_message(payload):
    event = payload.get('event', {})
    user_id = event.get('user')
    channel_id = event.get('channel')
    text = event.get('text')

    if BOT_ID != user_id:
        client.chat_postMessage(channel=channel_id, text=text)

if __name__ == '__main__':
    app.run(debug=True, port=5023)
 