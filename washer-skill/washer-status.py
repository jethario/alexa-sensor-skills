import boto3
import datetime
import json
import requests
import time
from flask import Flask
from flask_ask import Ask, statement, request, context, session, version
from pytz import timezone

app = Flask(__name__)
ask = Ask(app, '/')


@ask.intent("AMAZON.FallbackIntent")
@ask.intent('StatusIntent')
def status():
    try:
        client = boto3.client('cloudwatch', region_name='us-west-2')
        response = client.describe_alarms(
            AlarmNames=['Washer Finished']
        )
        for alarm in response['MetricAlarms']:
            if alarm['StateValue'] == 'ALARM':
                speech_text = "The washer is finished, or it gave out. Either way, it's not running."
            else:
                speech_text = "The washer is running, or it's possessed."
    except Exception as e:
        print(str(e))
        speech_text = "Something went wrong. Please check it out."
    print(speech_text)
    return statement(speech_text).simple_card('Washer', speech_text)


@ask.intent('MotionIntent')
def motion():
    try:
        client = boto3.client('cloudwatch', region_name='us-west-2')
        response = client.describe_alarms(
            AlarmNames=['Motion Detected']
        )
        for alarm in response['MetricAlarms']:
            if alarm['StateValue'] == 'ALARM':
                intro_text = "The washer started moving on"
            else:
                intro_text = "The washer stopped moving on"
            updated = alarm["StateUpdatedTimestamp"]
            time_text = updated.astimezone(
                timezone('US/Pacific')).strftime("%A, %I:%M %p")
            speech_text = "{} {}".format(intro_text, time_text)
    except Exception as e:
        print(str(e))
        speech_text = "Something went wrong. Please check it out."
    print(speech_text)
    return statement(speech_text).simple_card('Washer', speech_text)


if __name__ == '__main__':
    app.run()
