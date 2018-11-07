"""Test Specs:  

"""
# pylint: disable=E0402
import time
import unittest
import redis
import os
from threading import Thread

from .redis_helpers import wait_redis_update 
import enginecore.model.system_modeler as sm

from enginecore.state.state_managers import  StateManager
from enginecore.state.sensors import SensorRepository
from enginecore.state.redis_channels import RedisChannels

class ThermalTest(unittest.TestCase):


    """Test for the server load""" 
    @classmethod
    def setUpClass(cls):
        cls.redis_store = redis.StrictRedis(host='localhost', port=6379)

        server_attr = {
            'domain_name': 'an-a01n01', 
            'psu_num': 2, 
            'psu_load': [0.5, 0.5], 
            'power_consumption': 480, # amp -> 4
            'power_source': 120,
            'psu_power_consumption': 24,
            'psu_power_source': 120,
            'test_sensor_def': os.path.join(os.path.dirname(__file__), 'psuOnly.json')
        }

        attr = {}

        sm.drop_model()
        sm.create_outlet(1, attr)
        sm.create_outlet(2, attr)
        sm.create_ups(3, {
            'power_consumption': 240,
            'power_source': 120,
            'port': 1024
        })


        sm.create_server(4, server_attr, server_variation=sm.ServerVariations.ServerWithBMC)

        sm.link_assets(1, 3)
        sm.link_assets(32, 41)
        sm.link_assets(2, 42)

        StateManager.reload_model()
        time.sleep(5)


    def check_redis_values(self, expected_kv):
        for key, value in expected_kv.items():
            # check values
            r_key = key
            r_value = ThermalTest.redis_store.get(r_key)
            self.assertAlmostEqual(float(value), float(r_value), msg="asset [{}] = {}, expected({})".format(key, r_value, value))


    def test_outage(self):

        mains_down = {'mains-source': 0, '1-outlet': 0, '2-outlet':0, '3-ups':1, '41-psu':1, '42-psu':0}
        mains_up = {'mains-source': 1, '1-outlet': 1, '2-outlet':1, '3-ups':1, '41-psu':1, '42-psu':1}

        print('-> Simulating power outage')
        mains_t = Thread(target=wait_redis_update, args=(ThermalTest.redis_store, RedisChannels.mains_update_channel, {'mains-source': 0}, 1))
        state_t = Thread(target=wait_redis_update, args=(ThermalTest.redis_store, RedisChannels.state_update_channel, mains_down, 2))

        state_t.start()
        mains_t.start()

        StateManager.power_outage()

        mains_t.join()
        state_t.join()
        self.check_redis_values(mains_down)
        
        # restore power
        print('-> Restoring power...')
        mains_t = Thread(target=wait_redis_update, args=(ThermalTest.redis_store, RedisChannels.mains_update_channel, {'mains-source': 1}, 1))
        state_t = Thread(target=wait_redis_update, args=(ThermalTest.redis_store, RedisChannels.state_update_channel, mains_up, 2))

        state_t.start()
        mains_t.start()

        StateManager.power_restore()

        mains_t.join()
        state_t.join()
        self.check_redis_values(mains_up)


    def test_ambient(self):

        ambient_t = Thread(
            target=wait_redis_update, args=(ThermalTest.redis_store, RedisChannels.mains_update_channel, {'ambient': 22}, 1)
        )

        ambient_t.start()
        StateManager.set_ambient(22)
        ambient_t.join()
        self.assertAlmostEqual(22, StateManager.get_ambient())
        
        

    def test_ambient_affecting_sensors(self):

        print('-> Testing ambient affecting sensors...')

        ambient_t = Thread(
            target=wait_redis_update, args=(ThermalTest.redis_store, RedisChannels.mains_update_channel, {'ambient': 23}, 1)
        )

        ambient_t.start()
        StateManager.set_ambient(23)
        
        sensor_repo = SensorRepository(4)
        amb_sensor = sensor_repo.get_sensor_by_name('Ambient')

        ambient_t.join()
        time.sleep(2)

        self.assertEqual(int(StateManager.get_ambient()), int(amb_sensor.sensor_value))

        
        
if __name__ == '__main__':
    unittest.main()