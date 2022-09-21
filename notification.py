from retry import retry
from logs import logger
from urllib import request, parse


@retry(logger=logger, delay=2, tries=2)
def send_push_notification(message):
REMOVED
    message_json = {'text': message}
    data = parse.urlencode(message_json).encode()
    req = request.Request("https://api.chanify.net/v1/sender/" + token, data=data)
    request.urlopen(req)


if __name__ == "__main__":
    send_sms( 'testing')
