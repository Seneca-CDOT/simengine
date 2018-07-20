"""Test Specs:  
A Diamond shape model where a PDU powers both server PSUs

All Powered:            
--------------
                                    [4Amp]
    [4Amp]    [4Amp]    [2Amp]        | 
      |          |        |     |(Server)- 4Amp|   
    (out-1)->(pdu-2)->(pdu-21)->|(psu-41)- 2Amp|
                    ->(pdu-23)->|(psu-42)- 2Amp|
                          |   
                        [2Amp]         

"""


import time
import unittest
from threading import Thread
import redis
import enginecore.model.system_modeler as sm


from enginecore.state.state_managers import BMCServerStateManager, StateManager 

class ServerLoadTestDiamond(unittest.TestCase):


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
        sm.create_pdu(2, attr)
        sm.create_server(4, server_attr, server_variation='ServerWithBMC')

        sm.link_assets(1, 2)
        sm.link_assets(21, 41)
        sm.link_assets(23, 42)


    def check_redis_values(self, expected_kv, empty_msg_limit=10):
        
        pubsub = ServerLoadTestDiamond.redis_store.pubsub()
        pubsub.psubscribe('load-upd')

        CHECK = True
        keys_updated = []
        empty_msg = 0

        while CHECK:                                                              
            message = pubsub.get_message() 
                                                    
            if message and message['pattern'] == b"load-upd":
                data = message['data'].decode("utf-8")
                key, value = data.split('-')                                     

                self.assertAlmostEqual(expected_kv[int(key)], float(value))
                print("asset [{}] = {}".format(int(key), float(value))) 
                keys_updated.append(int(key))
                if len(keys_updated) == len(expected_kv.keys()):
                    CHECK = False                               
            else:
                empty_msg += 1

            if empty_msg == empty_msg_limit:
                self.fail("One of the values haven't been updated: {}".format(set(expected_kv.keys())-set(keys_updated)))


            time.sleep(0.2)

    def test_server_power(self):
        """
        Server Down:            
        --------------
                                        [0Amp]
          [0Amp]    [0Amp]   [0Amp]        | 
            |          |        |       |(Server)- 0Amp|   
            (out-1)->(pdu-2)->(out-21)->|(psu-41)- 0Amp|
                            ->(out-23)->|(psu-42)- 0Amp|
                                |   
                              [0Amp]        
        """

        try:
            
            # power down server
            print('-> Powering down server')
            thread = Thread(target=self.check_redis_values, args=({1:0, 2:0, 21:0, 23:0, 4:0, 41:0, 42:0},))
            thread.start()
            server = BMCServerStateManager({
                'key': 4, 
                'name': 'fedora27', 
                'powerConsumption': 480,
                'powerSource': 120
                }, 'serverwithbmc', notify=True)

            server.shut_down()
            thread.join()
            
            # power up server
            # print('-> Powering up server')
            # thread = Thread(target=self.check_redis_values, args=({1:2, 2:2, 3:2, 31:2, 4:4, 41:2, 42:2},))
            # thread.start()
            # server.power_up()
            # thread.join()

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

            # power down psu 1
            print('-> Powering down PSU 1')
            thread = Thread(target=self.check_redis_values, args=({1:0, 3:0, 31:0, 41:0, 2:4, 42:4},))
            thread.start()

            psu_1.shut_down()
            thread.join()

            # power up psu 1
            print('-> Bringing back PSU 1')
            thread = Thread(target=self.check_redis_values, args=({1:2, 2:2, 3:2, 31:2, 41:2, 42:2},))
            thread.start()

            psu_1.power_up()
            thread.join()

            # power down psu 1
            print('-> Powering down PSU 2')
            thread = Thread(target=self.check_redis_values, args=({1:4, 3:4, 31:4, 41:4, 2:0, 42:0},))
            thread.start()
            
            psu_2.shut_down()
            thread.join()

            # power up psu 2
            print('-> Bringing back PSU 2')
            thread = Thread(target=self.check_redis_values, args=({1:2, 2:2, 3:2, 31:2, 41:2, 42:2},))
            thread.start()

            psu_2.power_up()
            thread.join()

        except AssertionError as e: 
            self.fail(e)

        
if __name__ == '__main__':
    unittest.main()