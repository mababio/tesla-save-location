from retry import retry
from logs import logger
from urllib import request, parse
from config import settings


@retry(logger=logger, delay=2, tries=2)
def send_push_notification(message):
    token = settings['production']['key']['chanify']
    message_json = {'text': message}
    data = parse.urlencode(message_json).encode()
    req = request.Request("https://api.chanify.net/v1/sender/" + token, data=data)
    request.urlopen(req)


if __name__ == "__main__":
    send_push_notification('testing')
