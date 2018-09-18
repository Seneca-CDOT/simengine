"""Test Specs:  
A simple model with 2 outlets, 1 pdu, 1 static asset & a server with dual PSU
where power stream forks in 2 directions

All Powered:            
--------------
                                              [4Amp]
     [4Amp]             [4Amp]   [2Amp]         |
       |                   |       |       |(Server)- 4Amp|
    (out-1) -[:POWERS]->(pdu-3)->(pdu-31)->|(psu-41)- 2Amp|
                                    :-     |(psu-42)- 2Amp|<-(out-2)
                                    :-                          |
                                 (pdu-34)->(static-5)         [2Amp]
                                    |           |
                                  [2Amp]      [2Amp]
"""
# pylint: disable=E0402
import time
import unittest
import redis
from threading import Thread

from .redis_helpers import wait_redis_update 
import enginecore.model.system_modeler as sm

from enginecore.state.state_managers import BMCServerStateManager, StateManager, StaticDeviceStateManager

class ServerLoadTest(unittest.TestCase):


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
            'psu_power_source': 120
        }

        attr = {}

        sm.drop_model()
        sm.create_outlet(1, attr)
        sm.create_outlet(2, attr)

        sm.create_pdu(3, { 'port': 1024})
        sm.create_server(4, server_attr, server_variation=sm.ServerVariations.ServerWithBMC)
        sm.create_static(5, {
            'power_consumption': 240,
            'power_source': 120,
            'name': 'test'
        })

        sm.link_assets(1, 3)
        sm.link_assets(31, 41)
        sm.link_assets(33, 5)
        sm.link_assets(2, 42)

        StateManager.reload_model()
        time.sleep(3)


    def check_redis_values(self, expected_kv):
        for key, value in expected_kv.items():
            # check values
            r_key = key + ":load"
            r_value = ServerLoadTest.redis_store.get(r_key)
            self.assertAlmostEqual(float(value), float(r_value), msg="asset [{}] = {}, expected({})".format(key, r_value, value))
        


    def test_server_power(self):

        try:
            
            server_down = {'1-outlet': 2, '2-outlet':0, '3-pdu':2, '33-outlet':2, '31-outlet':0, '4-serverwithbmc':0, '41-psu':0, '42-psu':0}
            server_up = {'1-outlet': 4, '2-outlet':2, '3-pdu':4, '33-outlet':2, '31-outlet':2, '4-serverwithbmc':4, '41-psu':2, '42-psu':2}
    
            # power down server
            print('-> Powering down server')
            thread = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', server_down,7))
            thread.start()
            server = BMCServerStateManager({
                'key': 4, 
                'domainName': 'an-a01n01', 
                'powerConsumption': 480,
                'powerSource': 120
                }, 'serverwithbmc', notify=True)

            server.shut_down()
            thread.join()
            self.check_redis_values(server_down)
            
            # power up server
            print('-> Powering up server')
            thread = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', server_up,7))
            thread.start()
            server.power_up()
            thread.join()
            self.check_redis_values(server_up)

        except AssertionError as e: 
            self.fail(e)


    def test_static(self):
        static = StaticDeviceStateManager({ 'key': 5, 'name': 'test', 'powerConsumption': 240,'powerSource': 120}, 'staticasset', notify=True)
        static_up = {'1-outlet': 4, '2-outlet':2, '3-pdu':4, '31-outlet':2, '33-outlet':2, '4-serverwithbmc':4, '5-staticasset':2, '41-psu':2, '42-psu':2}
        static_down = {'1-outlet': 2, '2-outlet':2, '3-pdu':2, '31-outlet':2, '33-outlet':0, '4-serverwithbmc':4, '5-staticasset':0, '41-psu':2, '42-psu':2}

        print('-> Powering down Static Asset')
        thread = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', static_down, 4))
        thread.start()

        static.shut_down()
        thread.join()
        self.check_redis_values(static_down)

        print('-> Powering up Static Asset')
        thread = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', static_up, 4))
        thread.start()

        static.power_up()
        thread.join()
        self.check_redis_values(static_up)

        print('-> Powering up Static Asset')

    def test_server_psu(self):

        try:
            psu_1 = StateManager({ 'key': 41 }, 'psu', notify=True)
            psu_2 = StateManager({ 'key': 42 }, 'psu', notify=True)
            

            only_psu1_down = {'1-outlet': 2, '2-outlet':4, '3-pdu':2, '31-outlet':0, '33-outlet':2, '4-serverwithbmc':4, '41-psu':0, '42-psu':4}
            only_psu2_down = {'1-outlet': 6, '2-outlet':0, '3-pdu':6, '31-outlet':4, '33-outlet':2, '4-serverwithbmc':4, '41-psu':4, '42-psu':0}
            both_down = {'1-outlet': 2, '2-outlet':0, '3-pdu':2, '31-outlet':0, '33-outlet':2, '4-serverwithbmc':0, '41-psu':0, '42-psu':0}
            both_up = {'1-outlet': 4, '2-outlet':2, '3-pdu':4, '31-outlet':2, '33-outlet':2, '4-serverwithbmc':4, '41-psu':2, '42-psu':2}

            # power down psu 1
            print('-> Powering down PSU 1')
            thread = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', only_psu1_down, 6))
            thread.start()

            psu_1.shut_down()
            thread.join()
            self.check_redis_values(only_psu1_down)

            # power up psu 1
            print('-> Bringing back PSU 1')
            thread = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', both_up, 6))
            thread.start()

            psu_1.power_up()
            thread.join()
            self.check_redis_values(both_up)
            

            # power down psu 1
            print('-> Powering down PSU 2')
            thread = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', only_psu2_down, 6))
            thread.start()
            
            psu_2.shut_down()
            thread.join()
            self.check_redis_values(only_psu2_down)

            # power up psu 2
            print('-> Bringing back PSU 2')
            thread = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', both_up, 6))
            thread.start()

            psu_2.power_up()
            thread.join()
            self.check_redis_values(both_up)

            # power down both PSUs
            print('-> Powering down both PSUs')
            t1 = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', only_psu1_down, 5))
            t2 = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', both_down, 4))

            t1.start()
            psu_1.shut_down()
            
            t1.join()
            t2.start()
            psu_2.shut_down()
            t2.join()
            self.check_redis_values(both_down)

            # power up both PSUs
            print('-> Powering up both PSUs')
            t1 = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', only_psu2_down, 5))
            t2 = Thread(target=wait_redis_update, args=(ServerLoadTest.redis_store, 'load-upd', both_up, 4))

            t1.start()
            psu_1.power_up()
            
            t1.join()
            t2.start()
            psu_2.power_up()
            t2.join()
            self.check_redis_values(both_up)

        except AssertionError as e: 
            self.fail(e)

        

    def tearDown(self):
        pass #ServerLoadTest.app.stop()
        
if __name__ == '__main__':
    unittest.main()