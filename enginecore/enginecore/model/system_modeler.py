import json
import os
from enginecore.model.graph_reference import GraphReference


def create_asset(key, preset_file='presets/'):
    with open(preset_file) as f:
        data = json.load(f)

def create_pdu(key, preset_file= os.path.join(os.path.dirname(__file__), 'presets/apc_pdu.json')):
    with open(preset_file) as f, GraphReference().get_session() as session:
        data = json.load(f)
        outlet_count = data['OIDs']['OutletCount']

        session.run("\
        CREATE (pdu:Asset:PDU:SNMPSim { \
            name: $name,\
            key: $key,\
            staticOidFile: $oid_file\
        })", key=key, name=data['assetName'], oid_file=data['staticOidFile'])
        
        
         

