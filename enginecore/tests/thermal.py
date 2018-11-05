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

from enginecore.state.state_managers import BMCServerStateManager, StateManager, StaticDeviceStateManager

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
            'sensor_def': os.path.join(os.path.dirname(__file__), 'psuOnly.json')
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
        time.sleep(3)


    def check_redis_values(self, expected_kv):
        for key, value in expected_kv.items():
            # check values
            r_key = key
            r_value = ThermalTest.redis_store.get(r_key)
            self.assertAlmostEqual(float(value), float(r_value), msg="asset [{}] = {}, expected({})".format(key, r_value, value))


    def test_outage(self):

        mains_down = {'1-outlet': 0, '2-outlet':0, '3-ups':1, '41-psu':1, '42-psu':0}

        print('-> Simulating power outage')
        thread = Thread(target=wait_redis_update, args=(ThermalTest.redis_store, 'mains-upd', {'mains-source': 0}, 1))
        thread.start()

        StateManager.power_outage()

        thread.join()
        self.check_redis_values(mains_down)
        
        # # power up server
        # print('-> Powering up server')
        # thread = Thread(target=wait_redis_update, args=(ThermalTest.redis_store, 'load-upd', server_up, 7))
        # thread.start()
        # server.power_up()
        # thread.join()
        # self.check_redis_values(mains_down)



        
if __name__ == '__main__':
    unittest.main()