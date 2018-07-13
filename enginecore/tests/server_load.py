import os
import unittest
import enginecore.model.system_modeler as sm

from enginecore.state.state_managers import StateManger

class ServerLoadTest(unittest.TestCase):


    
    """Test for the server load"""
    def setUp(self):
        os.environ['SIMENGINE_STATIC_DATA'] = os.environ.get('SIMENGINE_STATIC_DATA', os.path.abspath("../data"))
        os.environ['SIMENGINE_IPMI_TEMPL'] = os.environ.get('SIMENGINE_IPMI_TEMPL', os.path.abspath("./ipmi_template"))
        os.environ['SIMENGINE_SNMP_SHA'] = os.environ.get(
            'SIMENGINE_SNMP_SHA', 
            str(os.popen('redis-cli script load "$(cat script/snmppub.lua)"').read())
        )

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

        sm.link_assets(1, 3)
        sm.link_assets(31, 41)
        sm.link_assets(2, 42)
        
    def test_initial_load(self):
        assets = StateManger.get_system_status(flatten=False)
        print(assets)
        load_out_1 = assets[1].get_load()
        load_out_2 = assets[2].get_load()
        load_pdu = assets[3].get_load()
        load_pdu_out = assets[31].get_load()
        load_server = assets[4].get_load()
        load_psu_1 = assets[41].get_load()
        load_psu_2 = assets[42].get_load()

        self.assertEqual(load_out_1, 2)
        self.assertEqual(load_out_2, 2)
        self.assertEqual(load_pdu, 2)

    def tearDown(self):
        pass #ServerLoadTest.app.stop()
        
if __name__ == '__main__':
    unittest.main()