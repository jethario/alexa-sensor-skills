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


def extremes(seconds):
    client = boto3.client('dynamodb', region_name='us-east-1')
    seconds_past = int(seconds)
    now = int(time.time())
    after_time = now - seconds_past

    response = client.query(
        TableName='pi_temperature',
        KeyConditionExpression='#n = :name AND #t >= :after',
        ExpressionAttributeValues={
            ":name": {
                "S": "garage"
            },
            ":after": {
                "N": str(after_time)
            }
        },
        ExpressionAttributeNames={
            '#n': 'name',
            '#t': 'timestamp'
        }
    )

    highest = 0
    lowest = 1000

    processed = 0
    for item in response['Items']:
        fahrenheit = int(item["fahrenheit"]["N"])
        if highest < fahrenheit:
            highest = fahrenheit
        if lowest > fahrenheit:
            lowest = fahrenheit
        processed = processed + 1

    return {
        "starting": str(after_time),
        "highest": str(highest),
        "lowest": str(lowest),
        "samples": str(processed)
    }


def latest():
    try:
        client = boto3.client('dynamodb', region_name='us-east-1')
        response = client.query(
            TableName='pi_temperature',
            KeyConditionExpression='#n = :name',
            ExpressionAttributeValues={
                ":name": {
                    "S": "garage"
                }
            },
            ExpressionAttributeNames={
                '#n': 'name'
            },
            Limit=1,
            ScanIndexForward=False
        )

        print(response)
        item = response['Items'][0]

        return {
            "timestamp": item["timestamp"]["N"],
            "fahrenheit": item["fahrenheit"]["N"]
        }
    except Exception as e:
        print(e)


def latest_by_name(name):
    try:
        client = boto3.client('dynamodb', region_name='us-east-1')
        response = client.query(
            TableName='pi_temperature',
            KeyConditionExpression='#n = :name',
            ExpressionAttributeValues={
                ":name": {
                    "S": name
                }
            },
            ExpressionAttributeNames={
                '#n': 'name'
            },
            Limit=1,
            ScanIndexForward=False
        )

        print(response)
        item = response['Items'][0]

        return {
            "timestamp": item["timestamp"]["N"],
            "fahrenheit": item["fahrenheit"]["N"]
        }
    except Exception as e:
        print(e)


@ask.intent('TemperatureIntent')
def temperature_intent():
    warning_threshold = 3600
    response = latest()
    print(response)
    reading = response
    timestamp = int(reading["timestamp"])
    current = int(time.time())
    dt = datetime.datetime.fromtimestamp(timestamp)
    time_text = dt.astimezone(timezone('US/Pacific')).strftime("%I:%M %p")
    speech_text = "The garage temperature was %s degrees at %s." % (
        reading["fahrenheit"], time_text)
    if current - timestamp > warning_threshold:
        speech_text = "%s The latest temperature sample is old. Please investigate." % speech_text
    print(speech_text)
    return statement(speech_text).simple_card('Garage', speech_text)


@ask.intent('ExtremesIntent')
def extremes_intent():
    response = extremes(60 * 60 * 24)
    print(response)
    reading = response
    if int(reading["samples"]) == 0:
        speech_text = "There were zero temperature samples from the last 24 hours. Please investigate."
    else:
        speech_text = "The garage temperature ranged from %s to %s degrees in the last 24 hours based on %s samples." % (
            reading["lowest"], reading["highest"], reading["samples"])
    print(speech_text)
    return statement(speech_text).simple_card('Garage', speech_text)


if __name__ == '__main__':
    app.run()
