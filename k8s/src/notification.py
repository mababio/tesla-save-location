from retry import retry
from logs import logger
from urllib import request, parse
import os

CHANIFY_KEY = os.environ.get('CHANIFY_KEY')


@retry(logger=logger, delay=2, tries=2)
def send_push_notification(message):
    message_json = {'text': message}
    data = parse.urlencode(message_json).encode()
    req = request.Request(f"https://api.chanify.net/v1/sender/{CHANIFY_KEY}", data=data)
    request.urlopen(req)


if __name__ == "__main__":
    send_push_notification('testing')
