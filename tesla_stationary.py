from datetime import datetime
from pytz import timezone
from retry import retry
import notification as chanify
import pymongo
from pymongo.server_api import ServerApi
import requests
from logs import logger
import notification

class tesla_stationary:

    def __init__(self,tesla_database):
        self.url_tesla_set_temp = "https://us-east4-ensure-dev-zone.cloudfunctions.net/function-tesla-set-temp"
        notification.send_push_notification('mababio3')
        self.url_tesla_info = "https://us-east4-ensure-dev-zone.cloudfunctions.net/tesla-info"
        self.db  = tesla_database

    @retry(logger=logger, delay=10, tries=3)
    def set_temp(self, temp='22.7778'):
        try:
            param = {"temp": temp}
            return requests.post(self.url_tesla_set_temp, json=param)
        except Exception as e:
            logger.warning('Issue calling ' + str(self.url_tesla_set_temp) + ': ' + str(e))
            raise

    @retry(logger=logger, delay=10, tries=3)
    def is_battery_good(self):
        try:
            battery_range = requests.get(self.url_tesla_info).json()['charge_state']['battery_range']
            return True if battery_range > 100 else False
        except Exception as e:
            logger.warning('Issue calling ' + str(self.url_tesla_info) + ': ' + str(e))
            raise

    @retry(logger=logger, delay=10, tries=3)
    def is_in_service(self):
        try:
            return requests.get(self.url_tesla_info).json()['in_service']
        except Exception as e:
            logger.warning('Issue calling ' + str(self.url_tesla_info) + ': ' + str(e))

    @retry(logger=logger, delay=10, tries=3)
    def is_parked(self,length=5):
        shift_state = requests.get(self.url_tesla_info).json()['drive_state']['shift_state']
        db_latlon_age_mins = self.__get_db_latlon_age()
        return True if shift_state is None and db_latlon_age_mins > length else False

    def __get_db_latlon_age(self):
        est = timezone('US/Eastern')
        db_latlon_timestamp_est = self.db['tesla_location'].find_one({'_id':'current'})['timestamp'].split('.')[0]
        db_latlon_timestamp_est_str = str(db_latlon_timestamp_est)
        db_latlon_timestamp_datetime_obj = datetime.strptime(db_latlon_timestamp_est_str, "%Y-%m-%d %H:%M:%S")

        current_timestamp_est_datetime_obj = datetime.now(est)
        current_timestamp_est_datetime_obj_formatted = str(current_timestamp_est_datetime_obj).split('.')[0]
        accepted_current_timestamp_est_datetime_obj = datetime.strptime(current_timestamp_est_datetime_obj_formatted, "%Y-%m-%d %H:%M:%S")

        timelapse = accepted_current_timestamp_est_datetime_obj - db_latlon_timestamp_datetime_obj
        return int(timelapse.total_seconds()/60) # this is in mins

    def is_tesla_parked_long(self):
        if not self.is_in_service() and self.is_battery_good() and self.is_parked(): #and self.is_on_home_street
            return True
        else:
            return False
