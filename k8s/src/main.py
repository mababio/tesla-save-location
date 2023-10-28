import requests
from logs import logger
import redis
import os
import json
# import notification

TESLA_DATA_SERVICES_BASE_URL = os.environ.get('TESLA_DATA_SERVICES_BASE_URL')


def listener():
    r = redis.Redis(
        host='redis-pub-sub',
        port=6379,
        decode_responses=True
    )

    mobile = r.pubsub()
    mobile.subscribe('save-location')

    for message in mobile.listen():
        data = message['data']
        # notification.send_push_notification(f'DEBUGG::::{data} and type:{type(data)}')
        save_gps(data)


def save_gps(pubsub_message):
    try:
        lat = json.loads(pubsub_message)['lat']
        lon = json.loads(pubsub_message)['lon']
        lat = float(lat)
        lon = float(lon)
        gps_json = {'lat':lat, 'lon':lon}
        # notification.send_push_notification(f'DEBUGGGGG::::{gps_json} this should be a json:{type(gps_json)}')
        requests.put(f"{TESLA_DATA_SERVICES_BASE_URL}/api/car/update/gps", json=gps_json)
        logger.info("hello_pubsub::::: Attempting to save lat lon to mongodb " + str(lat) + str(lon))
    except Exception as e:
        logger.error('ERROR ------> ' + str(e))


if __name__ == "__main__":
    listener()
