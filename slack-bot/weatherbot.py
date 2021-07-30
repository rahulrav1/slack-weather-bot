import os
import time
import re
import requests
import json
from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
API_KEY = "A79f8daMEcYMwTsecxfcE4HvrIwrF5FE"


def parse_bot_commands(slack_events):
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    default_response = "Not sure what you mean."
    response = requests.get(f'http://dataservice.accuweather.com/locations/v1/cities/search?apikey={API_KEY}&q={command}')
    json_resp = response.content.decode('utf-8').splitlines()[0]
    json_resp = json.loads(str(json_resp))
    loc_key = json_resp[0]["Key"]
    weather_data = requests.get(f'http://dataservice.accuweather.com/forecasts/v1/daily/1day/{loc_key}?apikey={API_KEY}')
    json_resp = weather_data.content.decode('utf-8').splitlines()[0]
    json_resp = json.loads(json_resp)
    json_resp = json_resp["DailyForecasts"][0]
    min_temperature = json_resp["Temperature"]["Minimum"]["Value"]
    max_temperature = json_resp["Temperature"]["Maximum"]["Value"]
    response = f'Minimum Temperature for {command}: {min_temperature}' + '\n' + f'Maximum Temperature for {command}: {max_temperature}'
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":
    print(os.environ.get('SLACK_BOT_TOKEN'))
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")