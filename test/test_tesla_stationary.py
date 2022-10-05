import datetime
from pytz import timezone
import pymongo
import requests
from pymongo.server_api import ServerApi
from src.tesla_stationary import TeslaStationary
from src.config import settings

client = pymongo.MongoClient(settings['URL']['mongodb'], username=settings['db_username'],
                             password=settings['db_password'], server_api=ServerApi('1'))
tesla_db = client['tesla']
obj = TeslaStationary(tesla_db)


def test_is_climate_on():
    assert type(obj.is_climate_on()) == bool


def test_get_climate_outside():
    assert type(obj.get_climate_outside()) == float


def test_set_climate_off():
    obj.set_temp(23)
    assert obj.is_climate_on() is True
    assert type(obj.set_climate_off()) == bool
    assert obj.is_climate_on() is False


def test_ideal_tesla_temp():
    outside_temp_f = obj.celsius_to_fahrenheit(obj.get_climate_outside())
    if outside_temp_f <= 50:
        assert obj.ideal_tesla_temp() == 22.7778
    elif outside_temp_f >= 77:
        assert obj.ideal_tesla_temp() == 21.6667
    else:
        assert obj.ideal_tesla_temp() is None


def test_is_climate_turned_on_via_automation():
    obj.set_temp(22)
    assert obj.is_climate_turned_on_via_automation() is True
    obj.set_climate_off()
    assert obj.is_climate_turned_on_via_automation() is False


def test_climate_turned_off_via_automation():
    obj.set_climate_off()
    obj.set_temp(22)
    obj.climate_turned_off_via_automation()
    assert obj.is_climate_turned_on_via_automation() is False


def test_climate_turned_on_via_automation_before():
    obj.set_climate_off()
    obj.set_temp(22)
    assert obj.climate_turned_on_via_automation_before() is True
    obj.climate_reset_for_automation()
    assert obj.climate_turned_on_via_automation_before() is False
    obj.set_climate_off()


def test_climate_reset_for_automation():
    obj.climate_reset_for_automation()
    assert tesla_db['tesla_climate_status'].find_one({'_id': 'enum'})['climate_state'] == 'at_user_well'
    assert tesla_db['tesla_climate_status'].find_one({'_id': 'enum'})['climate_turned_on_before'] == 'False'


def test_climate_turned_on_via_automation():
    obj.climate_turned_on_via_automation()
    assert tesla_db['tesla_climate_status'].find_one({'_id': 'enum'})['climate_state'] == 'climate_automation'
    assert tesla_db['tesla_climate_status'].find_one({'_id': 'enum'})['climate_turned_on_before'] == 'True'


def test_set_temp():
    obj.set_climate_off()
    assert obj.is_climate_on() is False
    obj.set_temp(22)
    assert obj.is_climate_on() is True
    assert obj.is_climate_turned_on_via_automation() is True
    obj.set_climate_off()


def test_is_battery_good():
    battery_range = requests.get(settings['URL']['tesla_info']).json()['charge_state']['battery_range']
    if battery_range <= 100:
        assert obj.is_battery_good() is False
    else:
        assert obj.is_battery_good() is True


def test_is_in_service():
    assert type(obj.is_in_service()) is bool


def test_is_parked():
    assert type(obj.is_parked()) is bool

    myquery = {"_id": 'current'}
    est = timezone('US/Eastern')
    one_min_old_datetime = datetime.datetime.now(est) - datetime.timedelta(minutes=10)
    new_values = {"$set": {"timestamp": str(one_min_old_datetime)}}
    tesla_db['tesla_location'].update_one(myquery, new_values)
    if obj.is_parked:
        assert obj.get_db_latlon_age() > settings['default']['min_parked_min']
        assert requests.get(settings['production']['URL']['tesla_info']).json()['drive_state']['shift_state'] is None


def test_get_db_latlon_age():
    myquery = {"_id": 'current'}
    est = timezone('US/Eastern')
    one_min_old_datetime = datetime.datetime.now(est) - datetime.timedelta(minutes=1)
    new_values = {"$set": {"timestamp": str(one_min_old_datetime)}}
    tesla_db['tesla_location'].update_one(myquery, new_values)
    assert obj.get_db_latlon_age() is 1


def test_is_tesla_parked_long():
    if not obj.is_in_service() and obj.is_battery_good() and obj.is_parked():
        assert obj.is_tesla_parked_long() is True
    else:
        assert obj.is_tesla_parked_long() is False


def test_is_tesla_home():
    tesla_db['tesla_location'].update_one({"_id": "current"}, {"$set": {"is_home": False}})
    assert type(obj.is_tesla_home()) is bool
    assert obj.is_tesla_home() is False
    tesla_db['tesla_location'].update_one({"_id": "current"}, {"$set": {"is_home": True}})
