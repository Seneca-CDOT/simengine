"""Test Specs:  
A simple model with 2 outlets, 1 pdu & a server with dual PSU
where power stream forks in 2 directions

All Powered:            
--------------
                                              [4Amp]
     [2Amp]             [2Amp]   [2Amp]         |
       |                   |       |       |(Server)- 4Amp|
    (out-1) -[:POWERS]->(pdu-3)->(pdu-31)->|(psu-41)- 2Amp|
                                 (out-2) ->|(psu-42)- 2Amp|
                                   |
                                 [2Amp]

"""

import redis
import time
import unittest
import enginecore.model.system_modeler as sm
from threading import Thread

from enginecore.state.state_managers import BMCServerStateManager, StateManager 

class ServerLoadTest(unittest.TestCase):


    """Test for the server load""" 
    @classmethod
    def setUpClass(cls):
        cls.redis_store = redis.StrictRedis(host='localhost', port=6379)

    def setUp(self):

        server_attr = {
            'domain_name': 'fedora27', 
            'psu_num': 2, 
            'psu_load': [0.5, 0.5], 
            'power_consumption': 480, # amp -> 4
            'power_source': 120
        }

        attr = {}

        sm.drop_model()
        sm.create_outlet(1, attr)
        sm.create_outlet(2, attr)

        sm.create_pdu(3, attr)
        sm.create_server(4, server_attr, server_variation='ServerWithBMC')
        sm.create_static(5, {
            'power_consumption': 240,
            'power_source': 120,
            'name': 'test'
        })

        sm.link_assets(1, 3)
        sm.link_assets(31, 41)
        sm.link_assets(33, 5)
        sm.link_assets(2, 42)


    def wait_redis_update(self, expected_kv, num_expected_updates, empty_msg_limit=10):
        
        pubsub = ServerLoadTest.redis_store.pubsub()
        pubsub.psubscribe('load-upd')

        CHECK = True
        keys_updated = {}
        num_updated = 0
        empty_msg = 0

        while CHECK:                                                              
            message = pubsub.get_message() 
                                                    
            if message and message['pattern'] == b"load-upd":
                data = message['data'].decode("utf-8")
                # print(message)    
                key, _ = data.split('-')                                     
                keys_updated[int(key)] = data
                num_updated += 1 

                if num_updated >= num_expected_updates:
                    CHECK = False                               
                                           
            else:
                empty_msg += 1

            if empty_msg == empty_msg_limit:
                self.fail("One of the values haven't been updated: {}".format(set(expected_kv.keys())-set(keys_updated.keys())))


            time.sleep(0.2)

            # time.sleep(0.2)
        return keys_updated
        
        # for k in keys_updated.keys():
        #     print(k, keys_updated[k])


    def check_redis_values(self, expected_kv):
        for key, value in expected_kv.items():
            # check values
            r_key = key + ":load"
            r_value = ServerLoadTest.redis_store.get(r_key)
            self.assertAlmostEqual(float(value), float(r_value), msg="asset [{}] = {}, expected({})".format(key, r_value, value))
        


    def test_server_power(self):
        """
        All Zero Load:            
        --------------
            0Amp       0Amp      0Amp     0Amp     |(Server)- 0Amp|
            (out-1) -[:POWERS]->(pdu-3)->(pdu-31)->|(psu-41)- 0Amp|
                                         (out-2) ->|(psu-42)- 0Amp|
                                          0Amp
        """

        try:
            
            server_down = {'1-outlet': 2, '2-outlet':0, '3-pdu':2, '33-outlet':2, '31-outlet':0, '4-serverwithbmc':0, '41-psu':0, '42-psu':0}
            server_up = {'1-outlet': 4, '2-outlet':2, '3-pdu':4, '33-outlet':2, '31-outlet':2, '4-serverwithbmc':4, '41-psu':2, '42-psu':2}
    
            # power down server
            print('-> Powering down server')
            thread = Thread(target=self.wait_redis_update, args=(server_down,7))
            thread.start()
            server = BMCServerStateManager({
                'key': 4, 
                'name': 'fedora27', 
                'powerConsumption': 480,
                'powerSource': 120
                }, 'serverwithbmc', notify=True)

            server.shut_down()
            thread.join()
            self.check_redis_values(server_down)
            
            # power up server
            print('-> Powering up server')
            thread = Thread(target=self.wait_redis_update, args=(server_up,7))
            thread.start()
            server.power_up()
            thread.join()
            self.check_redis_values(server_up)

        except AssertionError as e: 
            self.fail(e)

    def _test_server_psu(self):
        """
        PSU 1 down           
        --------------
            0Amp       0Amp      0Amp     0Amp     |(Server)- 4Amp|
            (out-1) -[:POWERS]->(pdu-3)->(pdu-31)->|(psu-41)- 0Amp|
                                         (out-2) ->|(psu-42)- 4Amp|
                                          4Amp
        All Powered:            
        --------------
            2Amp       2Amp      2Amp     2Amp     |(Server)- 4Amp|
            (out-1) -[:POWERS]->(pdu-3)->(pdu-31)->|(psu-41)- 2Amp|
                                         (out-2) ->|(psu-42)- 2Amp|
                                          2Amp
        
        PSU 2 down           
        --------------
            4Amp       4Amp      4Amp     4Amp     |(Server)- 4Amp|
            (out-1) -[:POWERS]->(pdu-3)->(pdu-31)->|(psu-41)- 4Amp|
                                         (out-2) ->|(psu-42)- 0Amp|
                                          0Amp      
        """
        try:
            psu_1 = StateManager({ 'key': 41 }, 'psu', notify=True)
            psu_2 = StateManager({ 'key': 42 }, 'psu', notify=True)
            

            only_psu1_down = {'1-outlet': 2, '2-outlet':4, '3-pdu':2, '31-outlet':0, '33-outlet':2, '4-serverwithbmc':4, '41-psu':0, '42-psu':4}
            only_psu2_down = {'1-outlet': 6, '2-outlet':0, '3-pdu':6, '31-outlet':4, '33-outlet':2, '4-serverwithbmc':4, '41-psu':4, '42-psu':0}
            both_down = {'1-outlet': 2, '2-outlet':0, '3-pdu':2, '31-outlet':0, '33-outlet':2, '4-serverwithbmc':0, '41-psu':0, '42-psu':0}
            both_up = {'1-outlet': 4, '2-outlet':2, '3-pdu':4, '31-outlet':2, '33-outlet':2, '4-serverwithbmc':4, '41-psu':2, '42-psu':2}

            # power down psu 1
            print('-> Powering down PSU 1')
            thread = Thread(target=self.wait_redis_update, args=(only_psu1_down, 7))
            thread.start()

            psu_1.shut_down()
            thread.join()
            self.check_redis_values(only_psu1_down)

            # power up psu 1
            print('-> Bringing back PSU 1')
            thread = Thread(target=self.wait_redis_update, args=(both_up, 6))
            thread.start()

            psu_1.power_up()
            thread.join()
            self.check_redis_values(both_up)
            

            # power down psu 1
            print('-> Powering down PSU 2')
            thread = Thread(target=self.wait_redis_update, args=(only_psu2_down, 7))
            thread.start()
            
            psu_2.shut_down()
            thread.join()
            self.check_redis_values(only_psu2_down)

            # power up psu 2
            print('-> Bringing back PSU 2')
            thread = Thread(target=self.wait_redis_update, args=(both_up, 6))
            thread.start()

            psu_2.power_up()
            thread.join()
            self.check_redis_values(both_up)

            # power down both PSUs
            print('-> Powering down both PSUs')
            t1 = Thread(target=self.wait_redis_update, args=(only_psu1_down, 7))
            t2 = Thread(target=self.wait_redis_update, args=(both_down, 4))

            t1.start()
            psu_1.shut_down()
            
            t1.join()
            t2.start()
            psu_2.shut_down()
            t2.join()
            self.check_redis_values(both_down)

            # power up both PSUs
            print('-> Powering up both PSUs')
            t1 = Thread(target=self.wait_redis_update, args=(only_psu2_down, 7))
            t2 = Thread(target=self.wait_redis_update, args=(both_up, 4))

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