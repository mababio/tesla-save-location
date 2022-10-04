import base64
import pymongo
from pymongo.server_api import ServerApi
from logs import logger
import json
from datetime import datetime
from pytz import timezone
from tesla_stationary import TeslaStationary
import notification
from config import settings


def get_db_client():
REMOVED
    return client['tesla']


db_client = get_db_client()
tesla_stationary_obj = TeslaStationary(db_client)


def update_gps_saved(lat, lon):
    myquery = {"_id": 'current'}
    est = timezone('US/Eastern')
    new_values = {"$set": {"lat": lat, "lon": lon, "timestamp": str(datetime.now(est))}}
    db_client['tesla_location'].update_one(myquery, new_values)


def save_location(lat, lon):
    try:
        return_saved_location = db_client['tesla_location'].find_one({'_id': 'current'})
        lat_current_saved = return_saved_location['lat']
        lon_current_saved = return_saved_location['lon']
        if lat == lat_current_saved and lon == lon_current_saved:
            logger.info('save_location: Current lat lon values are the same as mongodb values')
            if tesla_stationary_obj.is_tesla_parked_long() and not tesla_stationary_obj.is_climate_turned_on_via_automation() \
                    and not tesla_stationary_obj.climate_turned_on_via_automation_before() \
                    and tesla_stationary_obj.get_db_latlon_age() < settings['production']['max_parked_min']\
                    and not tesla_stationary_obj.is_tesla_home():
                logger.info('Cloud function that absorbed pubsub:::: calling set_temp')
                tesla_stationary_obj.set_temp()
            elif tesla_stationary_obj.is_climate_turned_on_via_automation() \
                    and tesla_stationary_obj.get_db_latlon_age() > settings['production']['max_parked_min']:
                try:
                    tesla_stationary_obj.set_climate_off()
                    notification.send_push_notification('Attempting to turn climate off')
                except Exception as e:
                    notification.send_push_notification('set_climate_off::::: Issue turning off climate after tesla'
                                                        'parked for long time' + str(e))
                    logger.error('set_climate_off::::: Issue turning off climate after tesla '
                                 'parked for long time' + str(e))
                raise
        else:
            update_gps_saved(lat, lon)
            if not tesla_stationary_obj.climate_turned_on_via_automation_before():
                pass
            else:
                tesla_stationary_obj.climate_reset_for_automation()
            logger.info('save_location: updating lat-long to mongodb ')
    except Exception as e:
        logger.error("save_location::: Issue saving location" + str(e))
        raise


def hello_pubsub(event, context):
    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        lat = json.loads(pubsub_message)['lat']
        lon = json.loads(pubsub_message)['lon']
        save_location(lat, lon)
        logger.info("hello_pubsub::::: Attempting to save lat lon to mongodb " + str(lat) + str(lon))
    except Exception as e:
        logger.error('ERROR ------> ' + str(e))

#
# if __name__ == "__main__":
#     save_location("40.670042", "-74.096599")
