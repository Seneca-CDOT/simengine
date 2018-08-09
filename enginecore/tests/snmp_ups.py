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
         

    def get_oid_value(self, oid):
        return subprocess.check_output('snmpget -c public -Oqv -v 1 127.0.0.1:1024 {}'.format(oid), shell=True)

    def test_ups_oids(self):
        all_up_state = {'1-outlet': 1, '3-ups':1, '35-outlet':1, '33-outlet':1, '31-outlet':1, '4-staticasset': 1, '5-staticasset': 1, '6-staticasset': 1}
        expected_state = all_up_state.copy()

        sm_out_1 = StateManager({'key': 1}, 'outlet', notify=True)
        sm_out_31 = StateManager({'key': 31}, 'outlet', notify=True)
        
        hp_battery_oid = '1.3.6.1.4.1.318.1.1.1.2.3.1.0' # Battery charge 100% * 10
        adv_battery_oid = '1.3.6.1.4.1.318.1.1.1.2.2.1.0' # Battery charge 100%
        output_status_oid = '1.3.6.1.4.1.318.1.1.1.4.1.1.0' # UPS Status: On-Battery, Powered etc.
        input_line_fail_cause_oid = '1.3.6.1.4.1.318.1.1.1.3.2.5.0' # Why switched to the Battery
        hp_output_load_oid = '1.3.6.1.4.1.318.1.1.1.4.3.3.0' # % from total capacity (mult by 10)
        adv_output_load_oid = '1.3.6.1.4.1.318.1.1.1.4.2.3.0' # % from total capacity 
        hp_output_current_oid = "1.3.6.1.4.1.318.1.1.1.4.3.4.0" # AMPS * 10
        adv_output_current_oid = '1.3.6.1.4.1.318.1.1.1.4.2.4.0'  # AMPS
        runtime_left_oid = '1.3.6.1.4.1.318.1.1.1.2.2.3.0'
        time_on_battery_oid = '1.3.6.1.4.1.318.1.1.1.2.1.2.0'
        
        print("-> Upstream power source is available")
        ### Test Upstrea power is On
        hp_battery = int(self.get_oid_value(hp_battery_oid))
        adv_battery = int(self.get_oid_value(adv_battery_oid))
        output_status = self.get_oid_value(output_status_oid)
        input_line_fail_cause = self.get_oid_value(input_line_fail_cause_oid)
        hp_output_load = int(self.get_oid_value(hp_output_load_oid))
        adv_output_load = int(self.get_oid_value(adv_output_load_oid))
        hp_output_current = int(self.get_oid_value(hp_output_current_oid))
        adv_output_current = int(self.get_oid_value(adv_output_current_oid))
        runtime_left = self.get_oid_value(runtime_left_oid)
        time_on_battery = self.get_oid_value(time_on_battery_oid)

        self.assertEqual(hp_battery, 1000)
        self.assertEqual(adv_battery, 100)
        self.assertEqual(output_status.decode().rstrip(), 'onLine') # 2 --> onLine
        self.assertEqual(input_line_fail_cause.decode().rstrip(), 'noTransfer')
        self.assertEqual(hp_output_load, int((((240*3)*100)/980)*10))
        self.assertEqual(adv_output_load, int((((240*3)*100)/980)))
        self.assertEqual(hp_output_current, int((240/120)*3*10))
        self.assertEqual(adv_output_current, int((240/120)*3))
        self.assertNotEqual(runtime_left.decode().rstrip(), '0:0:00:00.00')
        self.assertEqual(time_on_battery.decode().rstrip(), '0:0:00:00.00')

        ### Test Upstrea power is off (on-battery)
        print("-> Upstream power source is offline")
        
        # Check OIDs once load gets updated
        expected_state['1-outlet'] = 0

        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 2))
        thread.start()
        sm_out_1.shut_down()
        
        thread.join()
        time.sleep(1)

        drain_hp_battery = int(self.get_oid_value(hp_battery_oid))
        drain_adv_battery = int(self.get_oid_value(adv_battery_oid))
        drain_output_status = self.get_oid_value(output_status_oid)
        drain_input_line_fail_cause = self.get_oid_value(input_line_fail_cause_oid)

        self.assertTrue(drain_hp_battery < hp_battery)
        self.assertTrue(drain_adv_battery < adv_battery)
        self.assertEqual(drain_output_status.decode().rstrip(), 'onBattery') # 3 --> onBattery
        self.assertEqual(drain_input_line_fail_cause.decode().rstrip(), 'deepMomentarySag') 

        time.sleep(5) # -> 5 means blackout
        drain_input_line_fail_cause = self.get_oid_value(input_line_fail_cause_oid)
        self.assertEqual(drain_input_line_fail_cause.decode().rstrip(), 'blackout') 

        print("-> Powering down child component")
        
        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 3))
        thread.start()
        sm_out_31.shut_down()
        
        thread.join()
        time.sleep(1)

        hp_output_load = int(self.get_oid_value(hp_output_load_oid))
        adv_output_load = int(self.get_oid_value(adv_output_load_oid))
        hp_output_current = int(self.get_oid_value(hp_output_current_oid))
        adv_output_current = int(self.get_oid_value(adv_output_current_oid))
        new_runtime_left = self.get_oid_value(runtime_left_oid)
        new_time_on_battery = self.get_oid_value(time_on_battery_oid)

        self.assertEqual(hp_output_load, int((((240*2)*100)/980)*10))
        self.assertEqual(adv_output_load, int((((240*2)*100)/980)))
        self.assertEqual(hp_output_current, int((240/120)*2*10))
        self.assertEqual(adv_output_current, int((240/120)*2))
        self.assertNotEqual(new_runtime_left, runtime_left) # child is powered down -> battery is being drained
        self.assertNotEqual(new_time_on_battery, time_on_battery)

        # Check OIDs once load gets updated
        print("-> Power is restored")
        
        expected_state['1-outlet'] = 1

        thread = Thread(target=wait_redis_update, args=(PduSnmpTest.redis_store, 'load-upd', expected_state, 2))
        thread.start()
        sm_out_1.power_up()
        
        thread.join()

        charge_output_status = self.get_oid_value(output_status_oid)
        self.assertEqual(charge_output_status.decode().rstrip(), 'onLine') # back online!

        sm_out_31.power_up()

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