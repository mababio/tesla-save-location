from datetime import datetime
from pytz import timezone
from retry import retry
import requests
from logs import logger
import notification as notification
from config import settings
import math


class TeslaStationary:

    def __init__(self, tesla_database):
        self.url_tesla_control = settings['production']['URL']['tesla_control']
        self.url_tesla_info = settings['production']['URL']['tesla_info']
        self.db = tesla_database

    @retry(logger=logger, delay=10, tries=3)
    def is_climate_on(self):
        return requests.get(self.url_tesla_info).json()['climate_state']['is_climate_on']

    @retry(logger=logger, delay=10, tries=3)
    def get_climate_outside(self):
        return requests.get(self.url_tesla_info).json()['climate_state']['outside_temp']

    def set_climate_off(self):
        requests.get(self.url_tesla_control, json={'command': 'TURN_OFF_CLIMATE'})
        self.climate_turned_off_via_automation()
        return True

    def __fahrenheit_to_celsius(self, fahrenheit):
        return (fahrenheit - 32) * 5.0 / 9.0

    def celsius_to_fahrenheit(self, celsius):
        return math.ceil((celsius * 1.8) + 32)

    def ideal_tesla_temp(self):
        outside_temp_f = self.celsius_to_fahrenheit(self.get_climate_outside())
        if outside_temp_f <= 50:
            return self.__fahrenheit_to_celsius(73)
        elif outside_temp_f >= 77:
            return self.__fahrenheit_to_celsius(71)
        else:
            return None

    def is_climate_turned_on_via_automation(self):
        climate_state = self.db['tesla_climate_status'].find_one({'_id': 'enum'})['climate_state']
        return True if climate_state == 'climate_automation' else False

    def climate_turned_off_via_automation(self):
        myquery = {"_id": 'enum'}
        new_values = {"$set": {"climate_state": 'at_user_well'}}
        self.db['tesla_climate_status'].update_one(myquery, new_values)

    def climate_turned_on_via_automation_before(self):
        climate_turned_on_before = self.db['tesla_climate_status'].find_one({'_id': 'enum'})['climate_turned_on_before']
        return True if climate_turned_on_before == 'True' else False

    def climate_reset_for_automation(self):
        myquery = {"_id": 'enum'}
        new_values_state = {"$set": {"climate_state": 'at_user_well'}}
        new_values_turn_before = {"$set": {"climate_turned_on_before": 'False'}}
        self.db['tesla_climate_status'].update_one(myquery, new_values_state)
        self.db['tesla_climate_status'].update_one(myquery, new_values_turn_before)

    def climate_turned_on_via_automation(self):
        myquery = {"_id": 'enum'}
        new_values_state = {"$set": {"climate_state": 'climate_automation'}}
        new_values_turn_before = {"$set": {"climate_turned_on_before": 'True'}}
        self.db['tesla_climate_status'].update_one(myquery, new_values_state)
        self.db['tesla_climate_status'].update_one(myquery, new_values_turn_before)

    @retry(logger=logger, delay=10, tries=3)
    def set_temp(self, temp=None):
        if temp is None:
            temp = self.ideal_tesla_temp()
        else:
            temp = self.__fahrenheit_to_celsius(temp)
        if temp is None:
            return False
        else:
            if not self.is_climate_on():
                try:
                    #param = {"temp": temp}
                    param = {'command': 'SET_TEMP', 'args': {"temp": float(temp)}}
                    notification.send_push_notification('set_temp:::: calling set_temp cloud function')
                    requests.post(self.url_tesla_control, json=param)
                    notification.send_push_notification('Turned air on')
                    self.climate_turned_on_via_automation()
                    return True
                except Exception as e:
                    logger.warning('set_temp::::: Issue calling ' + str(self.url_tesla_control) + ': ' + str(e))
                    raise
            else:
                notification.send_push_notification('Climate is on already, no need to turn on')
                return False

    @retry(logger=logger, delay=10, tries=3)
    def is_battery_good(self):
        try:
            battery_range = requests.get(self.url_tesla_info).json()['charge_state']['battery_range']
            return True if battery_range > settings['production']['battery_min'] else False
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
    def is_parked(self, length=settings['production']['min_parked_min']):
        shift_state = requests.get(self.url_tesla_info).json()['drive_state']['shift_state']
        db_latlon_age_minutes = self.get_db_latlon_age()
        return True if shift_state is None and db_latlon_age_minutes > length else False

    def get_db_latlon_age(self):
        est = timezone('US/Eastern')
        db_latlon_timestamp_est = self.db['tesla_location'].find_one({'_id': 'current'})['timestamp'].split('.')[0]
        db_latlon_timestamp_est_str = str(db_latlon_timestamp_est)
        db_latlon_timestamp_datetime_obj = datetime.strptime(db_latlon_timestamp_est_str, "%Y-%m-%d %H:%M:%S")

        current_timestamp_est_datetime_obj = datetime.now(est)
        current_timestamp_est_datetime_obj_formatted = str(current_timestamp_est_datetime_obj).split('.')[0]
        accepted_current_timestamp_est_datetime_obj = datetime.strptime(current_timestamp_est_datetime_obj_formatted,
                                                                        "%Y-%m-%d %H:%M:%S")

        timelapse = accepted_current_timestamp_est_datetime_obj - db_latlon_timestamp_datetime_obj
        return int(timelapse.total_seconds()/60)  # this is in minutes

    def is_tesla_parked_long(self):
        if not self.is_in_service() and self.is_battery_good() and self.is_parked():  # and self.is_on_home_street
            return True
        else:
            return False

    def is_tesla_home(self):
        return self.db['tesla_location'].find_one({'_id': 'current'})['is_home']


if __name__ == "__main__":
    print('')

