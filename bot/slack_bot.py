import os
from pprint import pprint

import slack
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter


# Prepare apps
# run local tunnel first
# https://slackbotforsofaa2023.loca.lt

load_dotenv()
SLACK_TOKEN = os.environ['SLACK_TOKEN']
SIGNING_SECRET = os.environ['SIGNING_SECRET']

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)

client = slack.WebClient(token=SLACK_TOKEN)
BOT_ID = client.api_call("auth.test")['user_id']
# TODO: this should be saved in the db.
current_users = set()


# functions
def get_welcome_message():
    return [{
    'type': 'section',
    'text': {
        'type': 'mrkdwn',
        'text': (
                ':bubbles: *SoFAA에 오신 것을 환영합니다!* \n\n\n'
                '다음 명령어를 이용해서 디자인을 진행해보세요. (현재는 영어만 지원하고 있습니다.) \n\n\n'
                ':classical_building: */design 명령어와 --키워드1 --키워드2 --키워드3 ... 방식으로 디자인을 생성해보세요.* \n\n\n'
                'ex) /design --organic --futuristic --zaha hadid --sunset\n\n\n'
                ':classical_building: */develop 명령어와 --image_id 입력을 통해서 생성된 디자인을 디벨롭해보세요.* \n\n\n'
                'develop을 먼저 진행하시면 id가 이미지와 함께 제공됩니다. \n\n\n'
                'ex) /develop --id0123984213'
            )
        }
    }]

@slack_event_adapter.on('member_joined_channel')
def handle_member_joined_channel(payload):
    event = payload.get('event', {})
    user_id = event.get('user')

    if user_id not in current_users:
        current_users.add(user_id)
        welcome_msg = get_welcome_message()
        client.chat_postMessage(channel=f'@{user_id}', blocks=welcome_msg)


@slack_event_adapter.on('message')
def handle_explain_message(payload):
    event = payload.get('event', {})
    user_id = event.get('user')
    channel_id = event.get('channel')
    text = event.get('text')

    if text == '!설명':
        welcome_msg = get_welcome_message()
        client.chat_postMessage(channel=f'@{user_id}', blocks=welcome_msg)
        client.chat_postMessage(channel=channel_id, text=f":bubbles: SoFAA 사용법을 DM으로 보내드렸습니다.")


@app.route('/design', methods=['POST'])
def handle_design():
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text').strip("--").replace("--", ', ')
    client.chat_postMessage(channel=channel_id, text=f":bubbles: Designing :: [{text}]")

    return Response(), 200


@app.route('/develop', methods=['POST'])
def handle_develop():
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text')
    client.chat_postMessage(channel=channel_id, text=f":building_construction: Developing :: [{text}]")

    return Response(), 200


if __name__ == '__main__':
    app.run(debug=True, port=5023)
 