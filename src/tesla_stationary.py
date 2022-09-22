from datetime import datetime
from pytz import timezone
from retry import retry
import notification as chanify
import requests
from logs import logger
import notification


class TeslaStationary:

    def __init__(self, tesla_database):
        self.url_tesla_set_temp = "https://us-east4-ensure-dev-zone.cloudfunctions.net/function-tesla-set-temp"
        self.url_tesla_info = "https://us-east4-ensure-dev-zone.cloudfunctions.net/tesla-info"
        self.url_tesla_climate_off = "https://us-east4-ensure-dev-zone.cloudfunctions.net/function-tesla-turn-temp-off"
        self.db = tesla_database

    @retry(logger=logger, delay=10, tries=3)
    def is_climate_on(self):
        return requests.get(self.url_tesla_info).json()['climate_state']['is_climate_on']

    def set_climate_off(self):
        return requests.get(self.url_tesla_climate_off).json()['set'] == 'True'
        #https://us-east4-ensure-dev-zone.cloudfunctions.net/function-tesla-turn-temp-off

    def is_climate_turned_on_via_automation(self):
        climate_state = self.db['tesla_climate_status'].find_one({'_id':'enum'})['climate_state']
        if climate_state == 'climate_automation':
            return True
        else:
            False

    def climate_turned_off_via_automation(self):
        myquery = {"_id": 'enum'}
        new_values = {"$set": {"climate_state": 'at_user_well'}}
        self.db['tesla_climate_status'].update_one(myquery, new_values)

    def climate_turned_on_via_automation(self):
        myquery = {"_id": 'enum'}
        new_values = {"$set": {"climate_state": 'climate_automation'}}
        self.db['tesla_climate_status'].update_one(myquery, new_values)

    @retry(logger=logger, delay=10, tries=3)
    def set_temp(self, temp='21.1111'):
        if not self.is_climate_on():
            try:
                param = {"temp": temp}
                requests.post(self.url_tesla_set_temp, json=param)
                self.climate_turned_on_via_automation()
            except Exception as e:
                logger.warning('set_temp::::: Issue calling ' + str(self.url_tesla_set_temp) + ': ' + str(e))
                raise
        else:
            notification.send_push_notification('Climate is on already, no need to turn on')
        try:
            if self.__get_db_latlon_age() > 15 and self.is_climate_on() and self.is_climate_turned_on_via_automation:
                self.set_climate_off()
        except Exception as e:
            notification.send_push_notification('set_temp::::: Issue turning off climate after tesla parked for 15 mins')

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


if __name__ == "__main__":
    import pymongo
    from pymongo.server_api import ServerApi
REMOVED    tesla_database = client['tesla']
    obj = TeslaStationary(tesla_database)
    print(obj.is_climate_on())

