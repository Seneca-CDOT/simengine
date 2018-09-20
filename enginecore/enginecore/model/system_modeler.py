"""Add asset to a system model or update/create connection(s). 
This module provides high-level control over system model. 
"""
import json
import os
import secrets
import string
import random
import re
from enum import Enum

import libvirt
from enginecore.model.graph_reference import GraphReference

GRAPH_REF = GraphReference()

def _get_props_stm(attr, supported_attr=None):
    """Format dict attributes as neo4j props"""

    existing = dict(
        filter(lambda k: attr[k[0]] is not None and (not supported_attr or k[0] in supported_attr), attr.items())
    )
    return ','.join(map(lambda k: "{}: {}".format(_to_camelcase(k), repr(existing[k])), existing))


def _get_set_stm(attr, node_name="asset", supported_attr=None):
    """Format dict as neo4j set statement"""

    existing = dict(
        filter(lambda k: attr[k[0]] is not None and (not supported_attr or k[0] in supported_attr), attr.items())
    )
    return ','.join(map(lambda k: "{}.{}={}".format(node_name, _to_camelcase(k), repr(existing[k])), existing))


def _get_oid_desc_stm(oid_desc):
    """Format dict attributes as neo4j props"""
    return ','.join(map(lambda k: '{}: "{}"'.format(oid_desc[k], k), oid_desc))


def _add_psu(key, psu_index, attr):
    """Add a PSU to an existing server
    
    Args:
        key(int): server key psu will belong to
        psu_index(int): psu number
        attr(dict): psu attributes such as power_source, power_consumption, variation & draw
    """

    with GRAPH_REF.get_session() as session:

        query = []
        # find the server
        query.append("MATCH (asset:Asset {{ key: {} }})".format(key))

        # create a PSU
        attr['key'] = int("{}{}".format(key, psu_index))
        attr['name'] = 'psu' + str(psu_index)
        attr['type'] = 'psu'
        
        props_stm = _get_props_stm(attr)
        query.append("CREATE (psu:Asset:PSU:Component {{ {} }})".format(props_stm))

        # set relationships
        query.append("CREATE (asset)-[:HAS_COMPONENT]->(psu)") 
        query.append("CREATE (asset)-[:POWERED_BY]->(psu)") 

        session.run("\n".join(query))


def _to_camelcase(snake_string):
    """Convert snakecase to camelcase """    
    return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), snake_string)


def _generate_id(size=12, chars=string.ascii_uppercase + string.digits):
    """Ref: https://stackoverflow.com/a/23728630"""
    return ''.join(secrets.choice(chars) for _ in range(size))


def _generate_mac():
    """Generate a MAC address """
    return ''.join(random.choice('0123456789abcdef') for _ in range(12))

    
def configure_asset(key, attr):
    """Update existing properties
    
    Args:
        key(int): key of the asset to be configured
        attr(dict): asset props' updates
    """

    if 'func' in attr and attr['func']:
        del attr['func']

    if 'asset_key' in attr and attr['asset_key']:
        del attr['asset_key']

    with GRAPH_REF.get_session() as session:

        set_statement = _get_set_stm(attr)
        query = "MATCH (asset:Asset {{ key: {key} }}) SET {set_stm}".format(key=key, set_stm=set_statement)
        
        session.run(query)


def remove_link(source_key, dest_key):
    """Remove existing power connection
    
    Args:
        source_key(int): key of the parent asset
        dest_key(int): key of the asset powered by source_key
    """

    with GRAPH_REF.get_session() as session:
        session.run("""
        MATCH (src:Asset {key: $src_key})<-[power_link:POWERED_BY]-(dst:Asset {key: $dest_key})
        DELETE power_link
        """, src_key=source_key, dest_key=dest_key)


def link_assets(source_key, dest_key):
    """Power a component by another component 

    Args:
        source_key(int): key of the parent asset
        dest_key(int): key of the asset to be powered by the parent
    """

    with GRAPH_REF.get_session() as session:

        # Validate that the asset does not power already existing device
        result = session.run("""
            MATCH (src:Asset {key: $source_key})<-[:POWERED_BY]-(existing_dest:Asset) RETURN existing_dest
        """, source_key=source_key)

        record = result.single()
        if record:
            print('The source asset already powers an existing asset!')
            return

        result = session.run("""
            MATCH (src:Asset {key: $dest_key})-[:POWERED_BY]->(existing_src:Asset) RETURN existing_src
        """, dest_key=dest_key)

        record = result.single()
        if record:
            print('The destination asset is already powered by an existing asset!')
            return
        
        # Create a link
        result = session.run("""
        MATCH (src:Asset {key: $source_key})
        WHERE NOT src:PDU and NOT src:UPS and NOT src:Server and NOT src:ServerWithBMC
        MATCH (dst:Asset {key: $dest_key})
        WHERE NOT dst:Server and NOT dst:ServerWithBMC and (NOT dst:Component or dst:PSU) 
        CREATE (dst)-[r:POWERED_BY]->(src) return r as link
        """, source_key=source_key, dest_key=dest_key)
        
        record = result.single()

        if (not record) or ('link' not in dict(record)):
            print('Invalid link configuration was provided')


def create_outlet(key, attr):
    """Add outlet to the model 
    
     Args:
        key(int): unique key to be assigned
        attr(dict): asset properties
    """

    with GRAPH_REF.get_session() as session:
        attr['name'] = attr['name'] if 'name' in attr and attr['name'] else "out-{}".format(key)

        s_attr = ["name", "type", "key", "off_delay", "on_delay"]
        props_stm = _get_props_stm({**attr, **{'type': 'outlet', 'key': key}}, supported_attr=s_attr)
        session.run("CREATE (:Asset:Outlet {{ {} }})".format(props_stm))


class ServerVariations(Enum):
    """Supported variations of the server asset """
    Server = 1
    ServerWithBMC = 2

IPMI_LAN_DEFAULTS = {
    'user': 'ipmiusr',
    'password': 'test',
    'host': 'localhost',
    'port': 9001,
    'vmport': 9002
}
    

def _add_sensors(asset_key, preset_file=os.path.join(os.path.dirname(__file__), 'presets/sensors.json')):
    """Add sensors based on a preset file"""

    with open(preset_file) as preset_handler, GRAPH_REF.get_session() as session:        
        query = []

        query.append("MATCH (server:Asset {{ key: {} }})".format(asset_key))
        data = json.load(preset_handler)
        
        for sensor_type, sensor_specs in data.items():

            address_space_exists = 'addressSpace' in sensor_specs and sensor_specs['addressSpace']

            if address_space_exists:
                address_space = repr(sensor_specs['addressSpace'])
                query.append(
                    "CREATE (aSpace{}:AddressSpace {{ address: {} }})".format(
                        sensor_specs['addressSpace'], 
                        address_space
                    )
                )

            for idx, sensor in enumerate(sensor_specs['sensorDefinitions']):
                
                sensor_node = "{}{}".format(sensor_type, idx)

                if 'address' in sensor and sensor['address']:
                    addr = {'address': hex(int(sensor['address'], 16))}
                elif address_space_exists:
                    addr = {'index': idx}
                else:
                    raise KeyError("Missing address for a seonsor {}".format(sensor_type))

                s_attr = ["defaultValue", "name", "lnr", "lcr", "lnc", "unc", "ucr", "unr", "address", "index"]
                
                props = {**sensor['thresholds'], **sensor, **addr}
                props_stm = _get_props_stm(props, supported_attr=s_attr)

                query.append("CREATE (sensor{}:Sensor:{} {{ {} }})".format(sensor_node, sensor_type, props_stm))

                if not ('address' in sensor) or not sensor['address']:
                    query.append("CREATE (sensor{})-[:HAS_ADDRESS_SPACE]->(aSpace{})".format(
                        sensor_node,
                        sensor_specs['addressSpace']
                    ))

                query.append("CREATE (server)-[:HAS_SENSOR]->(sensor{})".format(sensor_node))

        # print("\n".join(query))
        session.run("\n".join(query))

def create_server(key, attr, server_variation=ServerVariations.Server):
    """Create a simulated server """

    if not attr['power_consumption']:
        raise KeyError('Server asset requires power_consumption attribute')
    if not attr['domain_name']:
        raise KeyError('Must provide VM name (domain name)')

    # Validate server domain name
    try:
        conn = libvirt.open("qemu:///system")
        conn.lookupByName(attr['domain_name'])
    except libvirt.libvirtError:
        raise KeyError('VM does not exist')
    finally:
        conn.close()


    with GRAPH_REF.get_session() as session:
        
        query = [] # cypher query

        attr['name'] = attr['name'] if 'name' in attr and attr['name'] else attr['domain_name']
        attr['type'] = server_variation.name.lower()
        attr['key'] = key

        s_attr = ["name", "domain_name", "type", "key", "off_delay", "on_delay", "power_consumption", "power_source"]
        props_stm = _get_props_stm(attr, supported_attr=s_attr)
        
        # create a server
        query.append("CREATE (server:Asset  {{ {} }}) SET server :{}".format(props_stm, server_variation.name))

        # set BMC-server specific attributes if type is bmc
        if server_variation == ServerVariations.ServerWithBMC:
            bmc_attr = {**IPMI_LAN_DEFAULTS, **attr} # merge

            set_stm = _get_set_stm(bmc_attr, node_name="server", supported_attr=IPMI_LAN_DEFAULTS.keys())
            query.append("SET {}".format(set_stm))

        session.run("\n".join(query))

        if server_variation == ServerVariations.ServerWithBMC:
            
            if 'sensor_def' in attr and attr['sensor_def']:
                sensor_file = attr['sensor_def']
            else:
                sensor_file = os.path.join(os.path.dirname(__file__), 'presets/sensors.json')
           
            _add_sensors(key, sensor_file)

        # add PSUs to the model
        for i in range(attr['psu_num']):
            psu_attr = {
                "power_consumption": attr['psu_power_consumption'], 
                "power_source": attr['psu_power_source'],
                "variation": server_variation.name.lower(),
                "draw": attr['psu_load'][i] if attr['psu_load'] else 1
            }
            _add_psu(key, psu_index=i+1, attr=psu_attr)


def create_ups(key, attr, preset_file=os.path.join(os.path.dirname(__file__), 'presets/apc_ups.json')):
    """Add UPS to the system model """

    preset_file = attr['snmp_preset'] if 'snmp_preset' in attr and attr['snmp_preset'] else preset_file

    with open(preset_file) as preset_handler, GRAPH_REF.get_session() as session:
        
        query = []
        data = json.load(preset_handler)

        attr['name'] = attr['name'] if 'name' in attr and attr['name'] else data['assetName']
        attr['runtime'] = json.dumps(data['modelRuntime'], sort_keys=True)

        s_attr = ["name", "type", "key", "off_delay", "on_delay", "staticOidFile", "port", "host",
                  "outputPowerCapacity", "minPowerOnBatteryLevel", "fullRechargeTime", "runtime",
                  "power_source", "power_consumption"]

        props_stm = _get_props_stm({**attr, **data, **{'key': key, 'type': 'ups'}}, supported_attr=s_attr)

        # create UPS asset
        query.append("CREATE (ups:Asset:UPS:SNMPSim {{ {} }})".format(props_stm))
        
        # add batteries (only one for now)
        query.append("CREATE (bat:UPSBattery:Battery { name: 'bat1', type: 'battery' })")
        query.append("CREATE (ups)-[:HAS_BATTERY]->(bat)")
        query.append("CREATE (ups)-[:POWERED_BY]->(bat)")

        # Add UPS OIDs
        for oid_key, oid_props in data["OIDs"].items():
            if oid_key == 'SerialNumber':
                oid_props['defaultValue'] = _generate_id()

            if oid_key == 'MAC':
                oid_props['defaultValue'] = _generate_mac()

            props = {**oid_props, **{'OIDName': oid_key}}
            props_stm = _get_props_stm(props, ["OID", "dataType", "defaultValue", "OIDName"])

            query.append("CREATE ({}:OID {{ {} }})".format(oid_key, props_stm))
            query.append("CREATE (ups)-[:HAS_OID]->({})".format(oid_key))

            if "oidDesc" in oid_props and oid_props["oidDesc"]:
                oid_desc = dict((y, x) for x, y in oid_props["oidDesc"].items())
                desc_stm = _get_oid_desc_stm(oid_desc)
                query.append("CREATE ({}Desc:OIDDesc {{ {} }})".format(oid_key, desc_stm))
                query.append("CREATE ({})-[:HAS_STATE_DETAILS]->({}Desc)".format(oid_key, oid_key))

            if oid_key == "PowerOff":
                query.append("CREATE (ups)-[:POWERED_BY]->({})".format(oid_key))

        # Set output outlets
        for i in range(data["numOutlets"]):

            props = {'name': 'out'+str(i+1), 'type': 'outlet', 'key': int("{}{}".format(key, str(i+1)))}
            props_stm = _get_props_stm(props)
            query.append("CREATE (out{}:Asset:Outlet:Component {{ {} }})".format(i, props_stm))
            query.append("CREATE (ups)-[:HAS_COMPONENT]->(out{})".format(i))
            query.append("CREATE (out{})-[:POWERED_BY]->(ups)".format(i))

        session.run("\n".join(query))


def create_pdu(key, attr, preset_file=os.path.join(os.path.dirname(__file__), 'presets/apc_pdu.json')):
    """Add PDU to the model """ 

    preset_file = attr['snmp_preset'] if 'snmp_preset' in attr and attr['snmp_preset'] else preset_file
    with open(preset_file) as preset_handler, GRAPH_REF.get_session() as session:

        query = []
        data = json.load(preset_handler)
        outlet_count = data['OIDs']['OutletCount']['defaultValue']
        
        attr['name'] = attr['name'] if 'name' in attr and attr['name'] else data['assetName']
        s_attr = ["name", "type", "key", "off_delay", "on_delay", "staticOidFile", "port", "host"]
        props_stm = _get_props_stm({**attr, **data, **{'key': key, 'type': 'pdu'}}, supported_attr=s_attr)

        # create PDU asset
        query.append("CREATE (pdu:Asset:PDU:SNMPSim {{ {} }})".format(props_stm))
        
        # Add PDU OIDS to the model
        for oid_key, oid_props in data["OIDs"].items():
            if oid_key == 'SerialNumber':
                oid_props['defaultValue'] = _generate_id()
            if oid_key == 'MAC':
                oid_props['defaultValue'] = _generate_mac()

            s_attr = ["OID", "OIDName", "defaultValue", "dataType"]
            props_stm = _get_props_stm({**oid_props, **{'OIDName': oid_key}}, supported_attr=s_attr)
            query.append("CREATE (:OID {{ {props_stm} }})<-[:HAS_OID]-(pdu)".format(props_stm=props_stm))


        # Outlet-specific OIDs
        for oid_key, oid_props in data["outletOIDs"].items():
            
            # For outlet state, Outlet asset will need to be created
            if oid_key == "OutletState":
                
                oid_desc = dict((y, x) for x, y in oid_props["oidDesc"].items())
                
                desc_stm = _get_oid_desc_stm(oid_desc)
                query.append("CREATE (oidDesc:OIDDesc {{ {} }})".format(desc_stm))

                for j in range(outlet_count):
                    
                    out_key = int("{}{}".format(key, str(j+1)))
                    props_stm = _get_props_stm({'key': out_key, 'name': 'out'+str(j+1), 'type': 'outlet'})

                    # create outlet per OID
                    query.append("CREATE (out{}:Asset:Outlet:Component {{ {} }})".format(out_key, props_stm))

                    # set outlet relationships
                    query.append("CREATE (out{})-[:POWERED_BY]->(pdu)".format(out_key))
                    query.append("CREATE (pdu)-[:HAS_COMPONENT]->(out{})".format(out_key))


                    # create OID associated with outlet & pdu
                    for oid_n, oid in enumerate(oid_props['OID']):

                        out_key = int("{}{}".format(key, str(j+1)))
                        oid = oid + "." + str(j+1)
                        oid_node_name = "{oid_name}{outlet_num}{oid_num}".format(
                            oid_name=oid_key, 
                            outlet_num=j, 
                            oid_num=oid_n
                        )
                        
                        props_stm = _get_props_stm({
                            'OID': oid, 
                            'OIDName': oid_key, 
                            'dataType': oid_props['dataType'], 
                            'defaultValue': oid_props['defaultValue']
                        })

                        query.append("CREATE ({oid_node_name}:OID {{ {props_stm} }})".format(
                            oid_node_name=oid_node_name, 
                            props_stm=props_stm))

                        # set the relationships (outlet powerd by state oid etc..)
                        query.append("CREATE (out{})-[:POWERED_BY]->({})".format(out_key, oid_node_name))
                        query.append("CREATE ({})-[:HAS_STATE_DETAILS]->(oidDesc)".format(oid_node_name))
                        query.append("CREATE (pdu)-[:HAS_OID]->({})".format(oid_node_name))
            else:
                oid = oid_props['OID']
                
                props_stm = _get_props_stm({
                    'OID': oid, 
                    'OIDName': oid_key, 
                    'dataType': oid_props['dataType'], 
                    'defaultValue': oid_props['defaultValue']
                })
                
                query.append("CREATE ({}:OID {{ {} }})".format(oid_key, props_stm))
                query.append("CREATE (pdu)-[:HAS_OID]->({})".format(oid_key))
                
        # print("\n".join(query))
        session.run("\n".join(query))


def create_static(key, attr):
    """Create Dummy static asset"""
    if not attr['power_consumption']:
        raise KeyError('Static asset requires power_consumption')
        
    with GRAPH_REF.get_session() as session:
        s_attr = ["name", "img_url", "type", "key", "off_delay", "on_delay", "power_consumption", "power_source"]
        props_stm = _get_props_stm({**attr, **{'type': 'staticasset', 'key': key}}, supported_attr=s_attr)
        session.run("CREATE (:Asset:StaticAsset {{ {} }})".format(props_stm))


def drop_model():
    """ Drop system model """
    with GRAPH_REF.get_session() as session:
        labels = ["Asset", "OID", "OIDDesc", "Battery", "StageLayout", "Sensor", "AddressSpace"]
        session.run("MATCH (a) WHERE {} DETACH DELETE a".format(" OR ".join(map("a:{}".format, labels))))
    

def delete_asset(key):
    """ Delete by key """
    with GRAPH_REF.get_session() as session:
        session.run("""MATCH (a:Asset { key: $key })
        OPTIONAL MATCH (a)-[:HAS_COMPONENT]->(s)
        OPTIONAL MATCH (a)-[:HAS_OID]->(oid)
        OPTIONAL MATCH (a)-[:HAS_BATTERY]->(b)
        OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(sd)
        DETACH DELETE a,s,oid,sd,b""", key=key)
