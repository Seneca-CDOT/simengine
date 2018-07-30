"""Test Specs:  
A simple model with 1 outlets, 1 pdu, 3 static asset 
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

        sm.create_pdu(3, attr)

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


    def test_outlet_power(self):

        all_up_state = {'1-outlet': 1, '3-pdu':1, '35-outlet':1, '33-outlet':1, '31-outlet':1}
        expected_state = all_up_state.copy()

        # power down server
        print('-> Powering down outlet through SNMP-set')
        expected_state['31-outlet'] = 0

        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 3))
        thread.start()

        self.set_outlet_state(1, 2) # switch off
        thread.join()
        self.check_redis_values(expected_state)


        print('-> Powering up outlet through SNMP-set')
        expected_state = all_up_state.copy()

        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 3))
        thread.start()

        self.set_outlet_state(1, 1) # switch on
        thread.join()
        self.check_redis_values(expected_state)


        print("-> Test reboot")
        expected_state = all_up_state.copy()

        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 3))
        thread.start()

        self.set_outlet_state(1, 3) # reboot
        thread.join()
        self.check_redis_values(expected_state)


        print("-> Test DelayOff")
        expected_state = all_up_state.copy()
        expected_state['33-outlet'] = 0
        expected_state['35-outlet'] = 0

        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 4))
        thread.start()

        self.set_outlet_state(3, 5) # delayedOff
        self.set_outlet_state(5, 5) # delayedOff
        
        thread.join()
        self.check_redis_values(expected_state)

        print("-> Test DelayOn")
        expected_state = all_up_state.copy()


        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 4))
        thread.start()

        self.set_outlet_state(3, 4) # delayedOn
        self.set_outlet_state(5, 4) # delayedOn
        
        thread.join()
        self.check_redis_values(expected_state)

    def test_pdu_load(self):
        all_up_state = {'1-outlet': 1, '3-pdu':1, '35-outlet':1, '33-outlet':1, '31-outlet':1}
        expected_state = all_up_state.copy()

        print("-> Test pdu load")

        sm_out_1 = StateManager({'key': 31}, 'outlet', notify=True)

        amp_oid = '1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.1'
        wattage_oid = '1.3.6.1.4.1.318.1.1.12.1.16.0'

        amp = self.get_oid_value(amp_oid)
        wattage = self.get_oid_value(wattage_oid)
        
        self.assertEqual(int(amp), 6*10)
        self.assertEqual(int(wattage), 6*120)

        expected_state['1-outlet'] = 0
        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 3))
        thread.start()
        sm_out_1.shut_down()
        
        thread.join()
        
        amp = self.get_oid_value(amp_oid)
        wattage = self.get_oid_value(wattage_oid)

        self.assertEqual(int(amp), 4*10)
        self.assertEqual(int(wattage), 4*120)
        
        sm_out_1.power_up()

    def test_pdu_uptime(self):
        
        print("-> Test pdu UPTIME")
        uptime_oid = '1.3.6.1.2.1.1.3.0'
        uptime_1 = self.get_oid_value(uptime_oid)
        time.sleep(1)
        uptime_2 = self.get_oid_value(uptime_oid)
        self.assertNotEqual(uptime_1, uptime_2)


    def tearDown(self):
        pass #PduSnmpTest.app.stop()
        
if __name__ == '__main__':
    unittest.main()