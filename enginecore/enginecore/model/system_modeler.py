"""Add asset to a system model or update/create connection(s). 
This module provides high-level control over system model. 
"""
import json
import os
import secrets
import libvirt
import string
import random
import re
from enum import Enum
from enginecore.model.graph_reference import GraphReference

graph_ref = GraphReference()

def _get_props_stm(attr, supported_attr=[]):
    """Format dict attributes as neo4j props"""

    existing = dict(
        filter(lambda k: attr[k[0]] != None and (not supported_attr or k[0] in supported_attr), attr.items())
    )
    return ','.join(map(lambda k: "{}: {}".format(_to_camelcase(k), repr(existing[k])), existing))


def _get_set_stm(attr, node_name="asset", supported_attr=[]):
    """Format dict as neo4j set statement"""

    existing = dict(
        filter(lambda k: attr[k[0]] != None and (not supported_attr or k[0] in supported_attr), attr.items())
    )
    return ','.join(map(lambda k: "{}.{}={}".format(node_name, _to_camelcase(k), repr(existing[k])), existing))


def _add_psu(key, psu_index, attr):
    """Add a PSU to an existing server
    
    Args:
        key(int): server key psu will belong to
        psu_index(int): psu number
        attr(dict): psu attributes such as power_source, power_consumption, variation & draw
    """

    with graph_ref.get_session() as session:

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


def _to_camelcase(s):
    return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), s)


def _generate_id(size=12, chars=string.ascii_uppercase + string.digits):
    """ Ref: https://stackoverflow.com/a/23728630"""
    return ''.join(secrets.choice(chars) for _ in range(size))


def _generate_mac():
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

    with graph_ref.get_session() as session:

        set_statement = _get_set_stm(attr)
        query = "MATCH (asset:Asset {{ key: {key} }}) SET {set_stm}".format(key=key, set_stm=set_statement)
        
        session.run(query)


def remove_link(source_key, dest_key):
    """Remove existing power connection
    
    Args:
        source_key(int): key of the parent asset
        dest_key(int): key of the asset powered by source_key
    """

    with graph_ref.get_session() as session:
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

    with graph_ref.get_session() as session:

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

        if (not record) or (not 'link' in dict(record)):
            print('Invalid link configuration was provided')


def create_outlet(key, attr):
    """Add outlet to the model 
    
     Args:
        key(int): unique key to be assigned
        attr(dict): asset properties
    """

    with graph_ref.get_session() as session:
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


    with graph_ref.get_session() as session:
        
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

        # add PSUs to the model
        for i in range(attr['psu_num']):
            psu_attr = {
                "power_consumption": attr['psu_power_consumption'], 
                "power_source": attr['psu_power_source'],
                "variation": server_variation.name.lower(),
                "draw": attr['psu_load'][i] if attr['psu_load'] else 1
            }
            _add_psu(key, psu_index=i+1, attr=psu_attr)

    
def set_properties(key, attr):
    with graph_ref.get_session() as session:
        if 'host' in attr and attr['host']:
            session.run("\
            MATCH (asset:Asset {key: $pkey})\
            SET asset.host=$host", pkey=key, host=attr['host'])
        
        if 'on_delay' in attr and attr['on_delay'] >= 0:
            session.run("\
            MATCH (asset:Asset {key: $pkey})\
            SET asset.onDelay=$on_delay", pkey=key, on_delay=attr['on_delay'])
        
        if 'off_delay' in attr and attr['off_delay'] >= 0:
            session.run("\
            MATCH (asset:Asset {key: $pkey})\
            SET asset.offDelay=$off_delay", pkey=key, off_delay=attr['off_delay'])

        if 'power_source' in attr and attr['power_source']:
            session.run("\
            MATCH (asset:Asset {key: $pkey})\
            SET asset.powerSource=$power_source", pkey=key, power_source=attr['power_source'])
        
        if 'power_consumption' in attr and attr['power_consumption']:
            session.run("\
            MATCH (asset:Asset {key: $pkey})\
            SET asset.powerConsumption=$power_consumption", pkey=key, power_consumption=attr['power_consumption'])
        
        if 'img_url' in attr and attr['img_url']:
            session.run("\
            MATCH (asset:Asset {key: $pkey})\
            SET asset.imgUrl=$img_url", pkey=key, img_url=attr['img_url'])



def create_ups(key, attr, preset_file=os.path.join(os.path.dirname(__file__), 'presets/apc_ups.json')):
    """Add UPS to the system model """

    preset_file = attr['snmp_preset'] if 'snmp_preset' in attr and attr['snmp_preset'] else preset_file

    with open(preset_file) as f, graph_ref.get_session() as session:
        data = json.load(f)

        name = attr['name'] if 'name' in attr and attr['name'] else data['assetName']
        
        session.run("\
        CREATE (:Asset:UPS:SNMPSim { \
            name: $name,\
            key: $key,\
            staticOidFile: $oid_file,\
            outputPowerCapacity: $pc,\
            minPowerOnBatteryLevel: $minbat,\
            fullRechargeTime: $rechargehrs, \
            type: 'ups',\
            runtime: $runtime,\
            port: $port \
        })", 
        key=key, 
        name=name,
        oid_file=data['staticOidFile'],
        pc=data['outputPowerCapacity'],
        minbat=data['minPowerOnBatteryLevel'],
        rechargehrs=data['fullRechargeTime'],
        runtime=json.dumps(data['modelRuntime'], sort_keys=True),
        port=attr['port']
        )

        set_properties(key, attr)
        
        # add batteries
        session.run("\
        MATCH (ups:UPS {key: $key})\
        CREATE (bat:UPSBattery:Battery { \
            name: $name,\
            type: 'battery'\
        })\
        CREATE (ups)-[:HAS_BATTERY]->(bat)\
        CREATE (ups)-[:POWERED_BY]->(bat)\
        ",key=key, name='bat1'
        )

        for k, v in data["OIDs"].items():
            if k == 'SerialNumber':
                v['defaultValue'] = _generate_id()

            if k == 'MAC':
                v['defaultValue'] = _generate_mac()

            if k == "BasicBatteryStatus":
                oid_desc = dict((y,x) for x,y in v["oidDesc"].items())
                query = "\
                CREATE (:OIDDesc {{\
                    OIDName: $name, \
                    {}: \"batteryNormal\", \
                    {}: \"batteryLow\"\
                }})".format(oid_desc["batteryNormal"], oid_desc["batteryLow"])

                session.run(query, name="{}-{}".format(k,key))

                session.run("\
                    MATCH (ups:UPS {key: $key})\
                    MATCH (oidDesc:OIDDesc {OIDName: $oid_desc})\
                    CREATE (oid:OID { \
                        OID: $oid,\
                        OIDName: $name,\
                        name: $name, \
                        defaultValue: $dv,\
                        dataType: $dt \
                    })\
                    CREATE (oid)-[:HAS_STATE_DETAILS]->(oidDesc)\
                    CREATE (ups)-[:HAS_OID]->(oid)\
                    ", 
                    key=key, 
                    oid=v['OID'], 
                    name=k,
                    dv=v['defaultValue'], 
                    dt=v['dataType'],
                    oid_desc="{}-{}".format(k,key))

            elif k == "BasicOutputStatus":
                oid_desc = dict((y,x) for x,y in v["oidDesc"].items())
                query = "\
                CREATE (:OIDDesc {{\
                    OIDName: $name, \
                    {}: \"onLine\", \
                    {}: \"onBattery\", \
                    {}: \"off\"\
                }})".format(
                    oid_desc["onLine"], 
                    oid_desc["onBattery"],
                    oid_desc["off"]
                )

                session.run(query, name="{}-{}".format(k,key))

                session.run("\
                    MATCH (ups:UPS {key: $key})\
                    MATCH (oidDesc:OIDDesc {OIDName: $oid_desc})\
                    CREATE (oid:OID { \
                        OID: $oid,\
                        OIDName: $name,\
                        name: $name, \
                        defaultValue: $dv,\
                        dataType: $dt \
                    })\
                    CREATE (oid)-[:HAS_STATE_DETAILS]->(oidDesc)\
                    CREATE (ups)-[:HAS_OID]->(oid)\
                    ", 
                    key=key, 
                    oid=v['OID'], 
                    name=k,
                    dv=v['defaultValue'], 
                    dt=v['dataType'],
                    oid_desc="{}-{}".format(k,key))

            elif k == "InputLineFailCause":
                oid_desc = dict((y,x) for x,y in v["oidDesc"].items())
                query = "\
                CREATE (:OIDDesc {{\
                    OIDName: $name, \
                    {}: \"noTransfer\", \
                    {}: \"blackout\", \
                    {}: \"deepMomentarySag\"\
                }})".format(
                    oid_desc["noTransfer"], 
                    oid_desc["blackout"],
                    oid_desc["deepMomentarySag"]
                )

                session.run(query, name="{}-{}".format(k,key))

                session.run("\
                    MATCH (ups:UPS {key: $key})\
                    MATCH (oidDesc:OIDDesc {OIDName: $oid_desc})\
                    CREATE (oid:OID { \
                        OID: $oid,\
                        OIDName: $name,\
                        name: $name, \
                        defaultValue: $dv,\
                        dataType: $dt \
                    })\
                    CREATE (oid)-[:HAS_STATE_DETAILS]->(oidDesc)\
                    CREATE (ups)-[:HAS_OID]->(oid)\
                    ", 
                    key=key, 
                    oid=v['OID'], 
                    name=k,
                    dv=v['defaultValue'], 
                    dt=v['dataType'],
                    oid_desc="{}-{}".format(k,key))

            elif k == "PowerOff":
                oid = v['OID']
                if 'oidDesc' in v:
                    oid_desc = dict((y,x) for x,y in v["oidDesc"].items())
                    query = "\
                    CREATE (PowerOffDetails:OIDDesc {{\
                        OIDName: $name, \
                        {}: \"switchOff\", \
                        {}: \"switchOffGraceful\"\
                    }})".format(oid_desc["switchOff"], oid_desc["switchOffGraceful"])

                    session.run(query, name="{}-{}".format(k,key))

                    session.run("\
                    MATCH (ups:UPS {key: $key})\
                    MATCH (oidDesc:OIDDesc {OIDName: $oid_desc})\
                    CREATE (oid:OID { \
                        OID: $oid,\
                        OIDName: $name,\
                        name: $name, \
                        defaultValue: $dv,\
                        dataType: $dt \
                    })\
                    CREATE (oid)-[:HAS_STATE_DETAILS]->(oidDesc)\
                    CREATE (ups)-[:POWERED_BY]->(oid)\
                    CREATE (ups)-[:HAS_OID]->(oid)\
                    ", 
                    key=key, 
                    oid=oid, 
                    name=k,
                    dv=v['defaultValue'], 
                    dt=v['dataType'],
                    oid_desc="{}-{}".format(k,key))
            else:
                session.run("\
                MATCH (ups:UPS {key: $key})\
                CREATE (oid:OID { \
                    OID: $oid,\
                    OIDName: $name,\
                    name: $name, \
                    defaultValue: $dv,\
                    dataType: $dt \
                })<-[:HAS_OID]-(ups)", key=key, oid=v['OID'], name=k, dv=v['defaultValue'], dt=v['dataType'])

        # Set output outlets
        for i in range(data["numOutlets"]):
            oid = v['OID'] + "." + str(i+1)

            session.run("\
            MATCH (ups:UPS {key: $key})\
            CREATE (out1:Asset:Outlet:Component { \
                name: $outname,\
                key: $outkey,\
                type: 'outlet'\
            })\
            CREATE (out1)-[:POWERED_BY]->(ups)\
            CREATE (ups)-[:HAS_COMPONENT]->(out1)\
            ", 
            key=key,
            outname='out'+str(i+1),
            outkey=int("{}{}".format(key,str(i+1))))


def _get_oid_desc_stm(oid_desc, oid_name):
    """Format dict attributes as neo4j props"""

    # existing = dict(
    #     filter(lambda k: attr[k[0]] != None and (not supported_attr or k[0] in supported_attr), oid_desc.items())
    # )
    return 'OIDName: "{}",'.format(oid_name) + ','.join(map(lambda k: '{}: "{}"'.format(oid_desc[k], k), oid_desc))


def create_pdu(key, attr, preset_file=os.path.join(os.path.dirname(__file__), 'presets/apc_pdu.json')):
    """Add PDU to the model """ 

    preset_file = attr['snmp_preset'] if 'snmp_preset' in attr and attr['snmp_preset'] else preset_file
    with open(preset_file) as f, graph_ref.get_session() as session:

        query = []
        data = json.load(f)
        outlet_count = data['OIDs']['OutletCount']['defaultValue']
        
        attr['name'] = attr['name'] if 'name' in attr and attr['name'] else data['assetName']
        s_attr = ["name", "type", "key", "off_delay", "on_delay", "staticOidFile", "port", "host"]
        props_stm = _get_props_stm({**attr, **data, **{'key': key, 'type': 'pdu'}}, supported_attr=s_attr)

        # create PDU asset
        query.append("CREATE (pdu:Asset:PDU:SNMPSim {{ {} }})".format(props_stm))
        
        # Add PDU OIDS to the model
        for k, v in data["OIDs"].items():
            if k == 'SerialNumber':
                v['defaultValue'] = _generate_id()
            if k == 'MAC':
                v['defaultValue'] = _generate_mac()

            props_stm = _get_props_stm({**v, **{'OIDName': k}}, supported_attr=["OID", "OIDName", "defaultValue", "dataType"])
            query.append("CREATE (:OID {{ {props_stm} }})<-[:HAS_OID]-(pdu)".format(oid_name=k, props_stm=props_stm))


        # Outlet-specific OIDs
        for k, v in data["outletOIDs"].items():
            
            # For outlet state, Outlet asset will need to be created
            if k == "OutletState":
                if 'oidDesc' in v:
                    oid_desc = dict((y,x) for x,y in v["oidDesc"].items())
                    
                    desc_stm = _get_oid_desc_stm(oid_desc, oid_name="{}-{}".format(k,key))
                    query.append("CREATE (oidDesc:OIDDesc {{ {} }})<-[:HAS_OID]-(pdu)".format(desc_stm))

                for j in range(outlet_count):
                    
                    out_key =  int("{}{}".format(key,str(j+1)))
                    props_stm = _get_props_stm({'key': out_key, 'name': 'out'+str(j+1), 'type': 'outlet'})

                    # create outlet per OID
                    query.append("CREATE (out{}:Asset:Outlet:Component {{ {} }})".format(out_key, props_stm))

                    # set outlet relationships
                    query.append("CREATE (out{})-[:POWERED_BY]->(pdu)".format(out_key))
                    query.append("CREATE (pdu)-[:HAS_COMPONENT]->(out{})".format(out_key))


                    # create OID associated with outlet & pdu
                    for oid_n, oid in enumerate(v['OID']):

                        out_key =  int("{}{}".format(key,str(j+1)))
                        oid = oid + "." + str(j+1)
                        oid_node_name = "{oid_name}{outlet_num}{oid_num}".format(oid_name=k, outlet_num=j, oid_num=oid_n)
                        
                        props_stm = _get_props_stm({'OID': oid, 'OIDName': k, 'dataType': v['dataType'], 'defaultValue': v['defaultValue']})
                        query.append("CREATE ({oid_node_name}:OID {{ {props_stm} }})".format(oid_node_name=oid_node_name, props_stm=props_stm))

                        # set the relationships (outlet powerd by state oid etc..)
                        query.append("CREATE (out{})-[:POWERED_BY]->({})".format(out_key, oid_node_name))
                        query.append("CREATE ({})-[:HAS_STATE_DETAILS]->(oidDesc)".format(oid_node_name))
                        query.append("CREATE (pdu)-[:HAS_OID]->({})".format(oid_node_name))
            else:
                oid = v['OID']
   
                props_stm = _get_props_stm({'OID': oid, 'OIDName': k, 'dataType': v['dataType'], 'defaultValue': v['defaultValue']})
                query.append("CREATE ({}:OID {{ {} }})".format(k, props_stm))
                query.append("CREATE (pdu)-[:HAS_OID]->({})".format(k))
                
        # print("\n".join(query))
        session.run("\n".join(query))


def create_static(key, attr):
    """Create Dummy static asset"""
    if not attr['power_consumption']:
        raise KeyError('Static asset requires power_consumption')
        
    with graph_ref.get_session() as session:
        s_attr = ["name", "img_url", "type", "key", "off_delay", "on_delay", "power_consumption", "power_source"]
        props_stm = _get_props_stm({**attr, **{'type': 'staticasset', 'key': key}}, supported_attr=s_attr)
        session.run("CREATE (:Asset:StaticAsset {{ {} }})".format(props_stm))


def drop_model():
    """ Drop system model """
    with graph_ref.get_session() as session:
        session.run("MATCH (a) WHERE a:Asset OR a:OID OR a:OIDDesc OR a:Battery OR a:StageLayout DETACH DELETE a")
    

def delete_asset(key):
    """ Delete by key """
    with graph_ref.get_session() as session:
        session.run("""MATCH (a:Asset { key: $key })
        OPTIONAL MATCH (a)-[:HAS_COMPONENT]->(s)
        OPTIONAL MATCH (a)-[:HAS_OID]->(oid)
        OPTIONAL MATCH (a)-[:HAS_BATTERY]->(b)
        OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(sd)
        DETACH DELETE a,s,oid,sd,b""", key=key)

