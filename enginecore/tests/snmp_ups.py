"""Test Specs:  
A simple model with 1 outlets, 1 ups, 3 static asset 
"""
# pylint: disable=E0402
import time
import unittest
import subprocess
import redis
from threading import Thread

from .redis_helpers import wait_redis_update 
import enginecore.model.system_modeler as sm

from enginecore.state.state_managers import StateManager, PDUStateManager

class PduSnmpTest(unittest.TestCase):


    """Test for the server load""" 
    @classmethod
    def setUpClass(cls):
        cls.redis_store = redis.StrictRedis(host='localhost', port=6379)

    def setUp(self):


        attr = {}

        sm.drop_model()
        sm.create_outlet(1, attr)

        sm.create_ups(3, attr)

        sm.create_static(4, {
            'power_consumption': 240,
            'power_source': 120,
            'name': 'test_1'
        })
        
        sm.create_static(5, {
            'power_consumption': 240,
            'power_source': 120,
            'name': 'test_2'
        })

        sm.create_static(6, {
            'power_consumption': 240,
            'power_source': 120,
            'name': 'test_3'
        })

        sm.link_assets(1, 3)
        sm.link_assets(31, 4)
        sm.link_assets(33, 5)
        sm.link_assets(35, 6)


    def check_redis_values(self, expected_kv):
        for key, value in expected_kv.items():
            # check values
            r_key = key
            r_value = PduSnmpTest.redis_store.get(r_key)
            self.assertEqual(float(value), float(r_value), msg="asset [{}] = {}, expected({})".format(key, r_value, value))
         

    def set_outlet_state(self, outlet_num, cmd):
        subprocess.check_output('snmpset -c public -v 1 127.0.0.1:1024  1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.{} i {}'.format(outlet_num, cmd), shell=True)


    def get_oid_value(self, oid):
        return subprocess.check_output('snmpget -c public -Oqv -v 1 127.0.0.1:1024 {}'.format(oid), shell=True)

    def test_ups_battery(self):
        all_up_state = {'1-outlet': 1, '3-ups':1, '35-outlet':1, '33-outlet':1, '31-outlet':1, '4-staticasset': 1, '5-staticasset': 1, '6-staticasset': 1}
        expected_state = all_up_state.copy()

        sm_out_1 = StateManager({'key': 1}, 'outlet', notify=True)
        
        hp_battery_oid = '1.3.6.1.4.1.318.1.1.1.2.3.1.0'
        adv_battery_oid = '1.3.6.1.4.1.318.1.1.1.2.2.1.0'


        hp_battery = int(self.get_oid_value(hp_battery_oid))
        adv_battery = int(self.get_oid_value(adv_battery_oid))

        self.assertEqual(hp_battery, 1000)
        self.assertEqual(adv_battery, 100)

        # Check OIDs once load gets updated
        expected_state['1-outlet'] = 0

        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 2))
        thread.start()
        sm_out_1.shut_down()
        
        thread.join()
        time.sleep(1)

        new_hp_battery = int(self.get_oid_value(hp_battery_oid))
        new_adv_battery = int(self.get_oid_value(adv_battery_oid))

        self.assertTrue(new_hp_battery < hp_battery)
        self.assertTrue(new_adv_battery < adv_battery)

    def test_ups_uptime(self):
        
        print("-> Test ups UPTIME")
        uptime_oid = '1.3.6.1.2.1.1.3.0'
        uptime_1 = self.get_oid_value(uptime_oid)
        time.sleep(1)
        uptime_2 = self.get_oid_value(uptime_oid)
        self.assertNotEqual(uptime_1, uptime_2)


    def tearDown(self):
        pass #PduSnmpTest.app.stop()
        
if __name__ == '__main__':
    unittest.main()