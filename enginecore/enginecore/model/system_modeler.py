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

def to_camelcase(s):
    return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), s)

def configure_asset(key, attr):

    if 'func' in attr and attr['func']:
        del attr['func']

    if 'asset_key' in attr and attr['asset_key']:
        del attr['asset_key']

    with graph_ref.get_session() as session:
        
        existing = dict(filter(lambda k: attr[k[0]], attr.items()))
        # print(existing)
        # existing = filter(lambda k: "asset.{}={}".format(k, repr(attr[k])) if attr[k] else None, attr)
        set_statement = ','.join(map(lambda k: "asset.{}={}".format(to_camelcase(k), repr(existing[k])), existing))
        query = "MATCH (asset:Asset {{ key: {key} }}) SET {set_stm}".format(key=key, set_stm=set_statement)
        
        session.run(query)


def link_assets(source_key, dest_key):
    """Power a component by another component """
    with graph_ref.get_session() as session:

        
        result = session.run("\
        MATCH (src:Asset {key: $source_key})\
        WHERE NOT src:PDU and NOT src:UPS and NOT src:Server and NOT src:ServerWithBMC\
        MATCH (dst:Asset {key: $dest_key})\
        WHERE NOT dst:Server and NOT dst:ServerWithBMC and (NOT dst:Component or dst:PSU) \
        CREATE (dst)-[r:POWERED_BY]->(src) return r as link\
        ", source_key=source_key, dest_key=dest_key)
        
        record = result.single()

        if (not record) or (not 'link' in dict(record)):
            print('Invalid link configuration was provided')

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
        CREATE (server:Asset { name: $name, domainName: $name, key: $key, type: $stype }) SET server :"+server_variation.name, 
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


def mac_generator():
    return ''.join(random.choice('0123456789abcdef') for _ in range(12))


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
            runtime: $runtime\
        })", 
        key=key, 
        name=name,
        oid_file=data['staticOidFile'],
        pc=data['outputPowerCapacity'],
        minbat=data['minPowerOnBatteryLevel'],
        rechargehrs=data['fullRechargeTime'],
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

            if k == 'MAC':
                v['defaultValue'] = mac_generator()

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




def create_pdu(key, attr, preset_file=os.path.join(os.path.dirname(__file__), 'presets/apc_pdu.json')):
    """Add PDU to the model """ 
    preset_file = attr['snmp_preset'] if 'snmp_preset' in attr and attr['snmp_preset'] else preset_file
    with open(preset_file) as f, graph_ref.get_session() as session:
        data = json.load(f)
        outlet_count = data['OIDs']['OutletCount']['defaultValue']
        name = attr['name'] if 'name' in attr and attr['name'] else data['assetName']
        
        session.run("\
        CREATE (:Asset:PDU:SNMPSim { \
            name: $name,\
            key: $key,\
            staticOidFile: $oid_file,\
            type: 'pdu'\
        })", key=key, name=name, oid_file=data['staticOidFile'])
        
        set_properties(key, attr)
        
        # Add PDU OIDS to the model
        for k, v in data["OIDs"].items():
            if k == 'SerialNumber':
                v['defaultValue'] = id_generator()

            if k == 'MAC':
                v['defaultValue'] = mac_generator()

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

                for j in range(outlet_count):
                    session.run("\
                        MATCH (pdu:PDU {key: $pkey})\
                        CREATE (out1:Asset:Outlet:Component { \
                            name: $outname,\
                            key: $outkey,\
                            type: 'outlet'\
                        })\
                        CREATE (out1)-[:POWERED_BY]->(pdu)\
                        CREATE (pdu)-[:HAS_COMPONENT]->(out1)\
                        ", 
                        pkey=key, 
                        outname='out'+str(j+1),
                        outkey=int("{}{}".format(key,str(j+1))))

                
                for j in range(outlet_count):
                    for oid in v['OID']:
                        oid = oid + "." + str(j+1)

                        session.run("\
                        MATCH (pdu:PDU {key: $pkey})\
                        MATCH (oidDesc:OIDDesc {OIDName: $oid_desc})\
                        MATCH (out1:Asset:Outlet:Component { key: $outkey })\
                        CREATE (oid:OID { \
                            OID: $oid,\
                            OIDName: $name,\
                            name: $name, \
                            defaultValue: $dv,\
                            dataType: $dt \
                        })\
                        CREATE (out1)-[:POWERED_BY]->(oid)\
                        CREATE (oid)-[:HAS_STATE_DETAILS]->(oidDesc)\
                        CREATE (pdu)-[:HAS_OID]->(oid)\
                        ", 
                        pkey=key, 
                        oid=oid, 
                        name=k,
                        dv=v['defaultValue'], 
                        dt=v['dataType'],
                        outname='out'+str(j+1),
                        oid_desc="{}-{}".format(k,key),
                        outkey=int("{}{}".format(key,str(j+1))))
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
        session.run("MATCH (a) WHERE a:Asset OR a:OID OR a:OIDDesc OR a:Battery OR a:StageLayout DETACH DELETE a")
    

def delete_asset(key):
    """ Delete by key """
    with graph_ref.get_session() as session:
        session.run("MATCH (a:Asset { key: $key }) \
        OPTIONAL MATCH (a)-[:HAS_COMPONENT]->(s) \
        OPTIONAL MATCH (a)-[:HAS_OID]->(oid) \
        OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(sd) \
        DETACH DELETE a,s,oid,sd", key=key)

