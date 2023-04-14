import os
from queue import Queue, Empty
from threading import Thread
import time
from pprint import pprint

import slack
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

from models import ArchiDiffusionModel

# Prepare apps
# run serveo first
# https://slackbotforsofaa2023.serveo.net

load_dotenv()
SLACK_TOKEN = os.environ['SLACK_TOKEN']
SIGNING_SECRET = os.environ['SIGNING_SECRET']

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SIGNING_SECRET, '/slack/events', app)

client = slack.WebClient(token=SLACK_TOKEN)
BOT_ID = client.api_call("auth.test")['user_id']
IMG_DIR = "/home/fastdh/server/SoFAA/bot/imgs_generated"
# TODO: this should be saved in the db.
current_users = set()

# set queue, model
task_queue = Queue()
processed_queue = Queue()
sofaa = ArchiDiffusionModel(batch_size=4, num_inference_steps=25)

# functions
def upload_file_to_slack_client(processed_queue):
    while True:
        task = processed_queue.get()
        task_type = task['type']
        img_names = task['img_names']
        channel_id = task['channel']
        prompt = task['prompt']
        thread_ts = task['thread_ts']
        user_id = task['user_id']
        
        if task_type == "develop":
            client.files_upload(
                title=prompt,
                file=f"{IMG_DIR}/{prompt}.jpg",
                channels=channel_id,
                initial_comment=f"다음 이미지로부터 디자인을 발전시켜 보았습니다.",
                thread_ts=thread_ts
            )

        for name in img_names:
            client.files_upload(
                title=prompt,
                file=f"{IMG_DIR}/{name}.jpg",
                channels=channel_id,
                initial_comment=f"다음 명령어로 디자인을 발전시켜 보세요: /develop --{name}",
                thread_ts=thread_ts
            )

        client.chat_postMessage(channel=channel_id,
                                thread_ts=thread_ts,
                                text=f":bubbles: <@{user_id}>님 요청하신 작업이 완료되었습니다.")
        
        processed_queue.task_done()

def get_welcome_message():
    return [{
    'type': 'section',
    'text': {
        'type': 'mrkdwn',
        'text': (
                ':bubbles: *SoFAA에 오신 것을 환영합니다!* \n\n'
                'SoFAA는 현재 영어만 지원하고 있으며, 디자인은 #design 채널에서 생성 가능합니다. \n\n'
                '#design 채널에서 다음 명령어를 입력해서 디자인을 진행해보세요. \n\n'
                ':art: */design 명령어와 키워드1, 키워드2, 키워드3 ... 방식으로 디자인을 생성해보세요.* \n\n'
                '키워드 내 띄어쓰기가 가능하고, 구체적인 묘사 또한 입력 가능합니다. \n\n'
                '아래 예시를 #design 채널에서 사용해보세요.\n\n'
                'ex) /design swimming pool in baroque style building, inside, highly detailed, eye level  \n\n'
                ':building_construction: */develop 명령어와 --image_id 입력을 통해서 생성된 디자인을 디벨롭해보세요.* \n\n'
                'design을 먼저 진행하시면 id가 이미지와 함께 제공됩니다. 원하시는 이미지 태그를 복사 붙혀넣기를 해보세요. \n\n'
                'ex) /develop --3S0N70H7KGMHLFIP \n\n'
                '각 명령어는 4장의 이미지를 생성합니다. \n\n'
                '생성 속도가 느리다면 조금만 기다려주세요. 개인 서버로 운영되고 있어서 처리 속도가 느릴 수 있습니다. \n\n'
                '문제가 생길 시 @dev_SoFAA 로 DM을 주시면 처리 도와드리겠습니다.'
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
        client.chat_postMessage(channel=channel_id, text=f":bubbles: <@{user_id}>님 SoFAA 사용법을 DM으로 보내드렸습니다.")


@app.route('/design', methods=['POST'])
def handle_design():
    data = request.form
    user_id = data.get('user_id')
    # TODO: for now upload images to channel directly, not reply in thread
    channel_id = data.get('channel_id')
    text = data.get('text')
    prompt = text.strip("--").replace("--", ', ')

    if channel_id != 'C0535RMS6U8':
        client.chat_postMessage(channel=channel_id, text=f":bubbles: 디자인 명령어는 #design 채널에서 사용해주세요.")
        return Response(), 200

    chat_response = client.chat_postMessage(
        channel=channel_id, 
        text=f":bubbles: Designing :: {text}"
        )
    
    task = {
        'type': 'design',
        'prompt': prompt,
        'channel': channel_id,
        'user_id': user_id,
        'thread_ts': chat_response.get('ts')
    }
    task_queue.put(task)

    return Response(), 200


@app.route('/develop', methods=['POST'])
def handle_develop():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    text = data.get('text').strip("--")

    if channel_id != 'C0535RMS6U8':
        client.chat_postMessage(channel=channel_id, text=f":bubbles: 디자인 명령어는 #design 채널에서 사용해주세요.")
        return Response(), 200

    chat_response = client.chat_postMessage(
        channel=channel_id, 
        text=f":building_construction: Developing :: [{text}]"
        )
    
    task = {
        'type': 'develop',
        'prompt': text,
        'channel': channel_id,
        'user_id': user_id,
        'thread_ts': chat_response.get('ts')
    }
    task_queue.put(task)

    return Response(), 200


if __name__ == '__main__':
    design_thread = Thread(target=sofaa.run, args=(task_queue, processed_queue))
    design_thread.start()
    upload_thread = Thread(target=upload_file_to_slack_client, args=(processed_queue,))
    upload_thread.start()
    
    app.run(debug=False, host='0.0.0.0', port=5023)
