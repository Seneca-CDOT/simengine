"""Add asset to a system model or update/create connection(s). This module provides high-level control over system model. """
import json
import os
from enginecore.model.graph_reference import GraphReference


def link_assets(source_key, dest_key):
    """Power a component by another component """
    with GraphReference().get_session() as session:
        session.run("\
        MATCH (src:Asset {key: $source_key})\
        MATCH (dst:Asset {key: $dest_key})\
        CREATE (dst)-[:POWERED_BY]->(src)\
        ", source_key=source_key, dest_key=dest_key)
        

def create_outlet(key):
    """Add outlet to the model """
    with GraphReference().get_session() as session:
        session.run("\
        CREATE (:Asset:Outlet { name: $name,  key: $key })", key=key, name="out-{}".format(key))


def create_pdu(key, preset_file=os.path.join(os.path.dirname(__file__), 'presets/apc_pdu.json')):
    """Add PDU to the model """    
    with open(preset_file) as f, GraphReference().get_session() as session:
        data = json.load(f)
        outlet_count = data['OIDs']['OutletCount']['defaultValue']

        session.run("\
        CREATE (:Asset:PDU:SNMPSim { \
            name: $name,\
            key: $key,\
            staticOidFile: $oid_file\
        })", key=key, name=data['assetName'], oid_file=data['staticOidFile'])
        
        
        # Add PDU OIDS to the model
        for k, v in data["OIDs"].items():
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
                        {}: \"switchOff\" \
                    }})\
                    ".format(oid_desc["switchOn"], oid_desc["switchOff"])
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
                    CREATE (out1:Asset:Outlet:SNMPComponent { \
                        name: $outname,\
                        key: $outkey\
                    })\
                    CREATE (out1)-[:POWERED_BY]->(pdu)\
                    CREATE (out1)-[:POWERED_BY]->(oid)\
                    CREATE (oid)-[:HAS_STATE_DETAILS]->(oidDesc)\
                    CREATE (pdu)-[:HAS_SNMP_COMPONENT]->(out1)\
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
            # TODO: else -> general OID


def create_static(key, attr):

    """Create Dummy static asset"""
    with GraphReference().get_session() as session:
        session.run("\
        CREATE (:Asset:StaticAsset { \
        name: $name, \
        key: $key,\
        imgUrl: $img_url, \
        powerSource: $psrc, \
        powerConsumption: $pcons })", 
        name=attr['name'], key=key, img_url=attr['img_url'], psrc=int(attr['power_source']), pcons=int(attr['power_consumption']))

