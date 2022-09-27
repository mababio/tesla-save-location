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

REMOVED
tesla_database = client['tesla']
tesla_stationary_obj = TeslaStationary(tesla_database)


def update_gps_saved(lat,lon):
    myquery = {"_id": 'current'}
    est = timezone('US/Eastern')
    new_values = {"$set": {"lat": lat, "lon": lon, "timestamp": str(datetime.now(est))}}
    tesla_database['tesla_location'].update_one(myquery, new_values)


def save_location(lat, lon):
    try:
        return_saved_location = tesla_database['tesla_location'].find_one({'_id': 'current'})
        lat_current_saved = return_saved_location['lat']
        lon_current_saved = return_saved_location['lon']
        if lat == lat_current_saved and lon == lon_current_saved:
            logger.info('save_location: Current lat lon values are the same as dbmongo values')
            if tesla_stationary_obj.is_tesla_parked_long() and not tesla_stationary_obj.is_climate_turned_on_via_automation() \
                    and not tesla_stationary_obj.climate_turned_on_via_automation_before():
                logger.info('Cloud function that absorbed pubsub:::: calling set_temp')
                tesla_stationary_obj.set_temp()
            elif tesla_stationary_obj.is_climate_turned_on_via_automation() \
                    and tesla_stationary_obj.get_db_latlon_age() > settings['production']['max_parked_min']:
                try:
                    tesla_stationary_obj.set_climate_off()
                    tesla_stationary_obj.climate_turned_off_via_automation()
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
            logger.info('save_location: updating latlong to dbmongo ')
    except Exception as e:
        logger.error("save_location::: Issue saving location" + str(e))
        raise


def hello_pubsub(event, context):
    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        lat = json.loads(pubsub_message)['lat']
        lon = json.loads(pubsub_message)['lon']
        save_location(lat, lon)
        logger.info("hello_pubsub::::: Attempting to save lat lon to mongdb " + str(lat) + str(lon))
    except Exception as e:
        logger.error('ERROR ------> ' + str(e))

#
# if __name__ == "__main__":
#     save_location("40.670042", "-74.096599")

