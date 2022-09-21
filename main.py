import base64
import pymongo
from pymongo.server_api import ServerApi
from logs import logger
import json
from datetime import datetime
from pytz import timezone
from tesla_stationary import tesla_stationary
import notification

REMOVED
tesla_database = client['tesla']


def save_location(lat, lon):
    try:
        return_saved_location = tesla_database['tesla_location'].find_one({'_id':'current'})
        lat_current_saved = return_saved_location['lat']
        lon_current_saved = return_saved_location['lon']
        if lat != lat_current_saved or lon != lon_current_saved:
            myquery = {"_id": 'current'}
            est = timezone('US/Eastern')
            new_values = {"$set": {"lat": lat, "lon": lon, "timestamp": str(datetime.now(est))}}
            tesla_database['tesla_location'].update_one(myquery, new_values)
            logger.info('save_location: updating latlong to dbmongo ')
        else:
            logger.info('save_location: Current lat lon values are the same as dbmongo values')
            tesla_stationary_obj = tesla_stationary(tesla_database)
            if tesla_stationary_obj.is_tesla_parked_long():
                tesla_stationary_obj.set_temp()
            else:
                logger.info("save_location::::: Not parked or not park long enough" )

    except Exception as e:
        logger.error("save_location::: Issue saving location")
        raise




def hello_pubsub(event, context):
    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        lat = json.loads(pubsub_message)['lat']
        lon = json.loads(pubsub_message)['lon']
        save_location(lat,lon)
        logger.info("hello_pubsub::::: Attempting to save lat lon to mongdb " + str(lat) + str(lon))
    except Exception as e:
        logger.error('ERROR ------> ' + str(e))
    
