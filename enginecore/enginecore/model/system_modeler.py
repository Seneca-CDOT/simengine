"""Add asset to a system model or update/create connection(s). This module provides high-level control over system model. """
import json
import os
import secrets
import libvirt
import string
from enum import Enum
from enginecore.model.graph_reference import GraphReference

graph_ref = GraphReference()

def link_assets(source_key, dest_key):
    """Power a component by another component """
    with graph_ref.get_session() as session:

        
        session.run("\
        MATCH (src:Asset {key: $source_key})\
        WHERE NOT src:PDU\
        MATCH (dst:Asset {key: $dest_key})\
        CREATE (dst)-[:POWERED_BY]->(src)\
        ", source_key=source_key, dest_key=dest_key)

def _add_psu(key, psu_index, draw_percentage=1):
    with graph_ref.get_session() as session:
        session.run("\
        MATCH (asset:Asset {key: $pkey})\
        CREATE (psu:Asset:PSU:Component { \
            name: $psuname,\
            key: $psukey,\
            draw: $draw,\
            type: 'psu'\
        })\
        CREATE (asset)-[:HAS_COMPONENT]->(psu)\
        CREATE (asset)-[:POWERED_BY]->(psu)", 
        pkey=key, psuname='psu'+psu_index, draw=draw_percentage, psukey=int("{}{}".format(key,psu_index)))
    

def create_outlet(key, attr):
    """Add outlet to the model """
    with graph_ref.get_session() as session:
        session.run("\
        CREATE (:Asset:Outlet { name: $name,  key: $key, type: 'outlet' })", key=key, name="out-{}".format(key))
        set_properties(key, attr)

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

    try:
        conn = libvirt.open("qemu:///system")
        conn.lookupByName(attr['domain_name'])
    except libvirt.libvirtError:
        raise KeyError('VM does not exist')
    finally:
        conn.close()


    with graph_ref.get_session() as session:
        
        session.run("\
        CREATE (server:Asset { name: $name,  key: $key, type: $stype }) SET server :"+server_variation.name, 
                    key=key, name=attr['domain_name'], stype=server_variation.name.lower())

        if server_variation == ServerVariations.ServerWithBMC:
            bmc_attr = {**IPMI_LAN_DEFAULTS, **attr}
            session.run("""
                MATCH (a:Asset {key: $key})
                SET a.user=$user, a.password=$password, a.host=$host, a.port=$port, a.vmport=$vmport
                """, 
                key=key, 
                user=bmc_attr['user'],
                password=bmc_attr['password'],
                host=bmc_attr['host'],
                port=bmc_attr['port'],
                vmport=bmc_attr['vmport']              
            )

        
        set_properties(key, attr)
        for i in range(attr['psu_num']):
            _add_psu(key, str(i+1), attr['psu_load'][i] if attr['psu_load'] else 1)

    
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

def id_generator(size=12, chars=string.ascii_uppercase + string.digits):
    """ Ref: https://stackoverflow.com/a/23728630"""
    return ''.join(secrets.choice(chars) for _ in range(size))


def create_ups(key, attr, preset_file=os.path.join(os.path.dirname(__file__), 'presets/apc_ups.json')):
    """Add UPS to the system model """
    with open(preset_file) as f, graph_ref.get_session() as session:
        data = json.load(f)

        session.run("\
        CREATE (:Asset:UPS:SNMPSim { \
            name: $name,\
            key: $key,\
            staticOidFile: $oid_file,\
            type: 'ups',\
            runtime: $runtime\
        })", 
        key=key, 
        name=data['assetName'],
        oid_file=data['staticOidFile'],
        runtime= json.dumps(data['modelRuntime'], sort_keys=True)
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
                v['defaultValue'] = id_generator()

            if k == "BasicBatteryStatus":
                oid_desc = dict((y,x) for x,y in v["oidDesc"].items())
                query = "\
                CREATE (PowerOffDetails:OIDDesc {{\
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




def create_pdu(key, attr, preset_file=os.path.join(os.path.dirname(__file__), 'presets/apc_pdu.json')):
    """Add PDU to the model """    
    with open(preset_file) as f, graph_ref.get_session() as session:
        data = json.load(f)
        outlet_count = data['OIDs']['OutletCount']['defaultValue']

        session.run("\
        CREATE (:Asset:PDU:SNMPSim { \
            name: $name,\
            key: $key,\
            staticOidFile: $oid_file,\
            type: 'pdu'\
        })", key=key, name=data['assetName'], oid_file=data['staticOidFile'])
        
        set_properties(key, attr)
        
        # Add PDU OIDS to the model
        for k, v in data["OIDs"].items():
            if k == 'SerialNumber':
                v['defaultValue'] = id_generator()

            session.run("\
            MATCH (pdu:PDU {key: $pkey})\
            CREATE (oid:OID { \
                OID: $oid,\
                OIDName: $name,\
                name: $name, \
                defaultValue: $dv,\
                dataType: $dt \
            })<-[:HAS_OID]-(pdu)", pkey=key, oid=v['OID'], name=k, dv=v['defaultValue'], dt=v['dataType'])

        # Outlet-specific OIDs
        for k, v in data["outletOIDs"].items():
            if k == "OutletState":
                if 'oidDesc' in v:
                    oid_desc = dict((y,x) for x,y in v["oidDesc"].items())
                    query = "\
                    CREATE (OutletStateDetails:OIDDesc {{\
                        OIDName: $name, \
                        {}: \"switchOn\",\
                        {}: \"switchOff\", \
                        {}: \"immediateReboot\",\
                        {}: \"delayedOn\",\
                        {}: \"delayedOff\"\
                    }})\
                    ".format(
                        oid_desc["switchOn"], 
                        oid_desc["switchOff"], 
                        oid_desc["immediateReboot"],
                        oid_desc["delayedOn"],
                        oid_desc["delayedOff"]
                    )

                    session.run(query, name="{}-{}".format(k,key))

                for i in range(outlet_count):
                    oid = v['OID'] + "." + str(i+1)

                    session.run("\
                    MATCH (pdu:PDU {key: $pkey})\
                    MATCH (oidDesc:OIDDesc {OIDName: $oid_desc})\
                    CREATE (oid:OID { \
                        OID: $oid,\
                        OIDName: $name,\
                        name: $name, \
                        defaultValue: $dv,\
                        dataType: $dt \
                    })\
                    CREATE (out1:Asset:Outlet:Component { \
                        name: $outname,\
                        key: $outkey,\
                        type: 'outlet'\
                    })\
                    CREATE (out1)-[:POWERED_BY]->(pdu)\
                    CREATE (out1)-[:POWERED_BY]->(oid)\
                    CREATE (oid)-[:HAS_STATE_DETAILS]->(oidDesc)\
                    CREATE (pdu)-[:HAS_COMPONENT]->(out1)\
                    CREATE (pdu)-[:HAS_OID]->(oid)\
                    ", 
                    pkey=key, 
                    oid=oid, 
                    name=k,
                    dv=v['defaultValue'], 
                    dt=v['dataType'],
                    outname='out'+str(i+1),
                    oid_desc="{}-{}".format(k,key),
                    outkey=int("{}{}".format(key,str(i+1))))
            else:
                oid = v['OID']
                session.run("\
                    MATCH (pdu:PDU {key: $pkey})\
                    CREATE (oid:OID { \
                        OID: $oid,\
                        OIDName: $name,\
                        name: $name, \
                        defaultValue: $dv,\
                        dataType: $dt \
                    })\
                    CREATE (pdu)-[:HAS_OID]->(oid)\
                    ", 
                    pkey=key, 
                    oid=oid, 
                    name=k,
                    dv=v['defaultValue'], 
                    dt=v['dataType'])

def create_static(key, attr):
    """Create Dummy static asset"""
    if not attr['power_consumption']:
        raise KeyError('Static asset requires power_consumption')
        
    with graph_ref.get_session() as session:
        session.run("\
        CREATE (:Asset:StaticAsset { \
        name: $name, \
        type: 'staticasset', \
        key: $key})", 
        name=attr['name'], key=key)
        set_properties(key, attr)

def drop_model():
    """ Drop system model """
    with graph_ref.get_session() as session:
        session.run("MATCH (a) WHERE a:Asset OR a:OID OR a:OIDDesc OR a:Battery DETACH DELETE a")
    
def delete_asset(key):
    """ Delete by key """
    with graph_ref.get_session() as session:
        session.run("MATCH (a:Asset { key: $key }) \
        OPTIONAL MATCH (a)-[:HAS_COMPONENT]->(s) \
        OPTIONAL MATCH (a)-[:HAS_OID]->(oid) \
        OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(sd) \
        DETACH DELETE a,s,oid,sd", key=key)

