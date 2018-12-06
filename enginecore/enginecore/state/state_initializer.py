"""Initialize redis state based on reference model """
import os
import tempfile
import shutil

import redis

from enginecore.model.graph_reference import GraphReference
from enginecore.state.utils import format_as_redis_key, get_asset_type


def clear_temp():
    """All app data is stored in /tmp/simengine (which is cleared on restart)"""
    sys_temp = tempfile.gettempdir()
    simengine_temp = os.path.join(sys_temp, 'simengine')
    if os.path.exists(simengine_temp):
        for the_file in os.listdir(simengine_temp):
            file_path = os.path.join(simengine_temp, the_file)    
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): 
                shutil.rmtree(file_path)
    else:
        os.makedirs(simengine_temp)


def initialize(force_snmp_init=False):
    """ Initialize redis state using topology defined in the graph db """

    graph_ref = GraphReference()
    redis_store = redis.StrictRedis(host='localhost', port=6379)

    results = graph_ref.get_session().run( # TODO: context manager
        """
        MATCH (asset:Asset) OPTIONAL MATCH (asset:Asset)-[:HAS_OID]->(oid)
        return asset, collect(oid) as oids
        """
    )

    for record in results:
        try:

            asset_type = get_asset_type(record['asset'].labels)
            asset_key = str(record['asset'].get('key'))

            init_from_snmprec = (not redis_store.exists("{}-{}".format(asset_key, asset_type))) or force_snmp_init
            redis_store.set("{}-{}".format(asset_key, asset_type), "1")
            formatted_key = asset_key.zfill(10)
            temp_ordering_key = formatted_key + '-temp_oids_ordering'

            graph_oids = {}
            for oid in record['oids']: # loop over oids that are defined in the graph db
                graph_oids[oid.get('OID')] = {
                    'dtype': oid.get('dataType'),
                    'value': oid.get('defaultValue')
                }            

            # Set-up in the SNMPSim format
            if 'SNMPSim' in record['asset'].labels and record['oids'] and init_from_snmprec:

                # Read a file containing static .snmprec data
                static_oid_file = record['asset'].get('staticOidFile')
                static_oid_path = os.path.join(os.environ.get('SIMENGINE_STATIC_DATA'), static_oid_file)

                with open(static_oid_path, "r") as sfile_handler:  
                    for line in sfile_handler:

                        oid, dtype, value = line.replace('\n', '').split('|')
                        if oid in graph_oids:
                            dtype = graph_oids[oid]['dtype']
                            value = graph_oids[oid]['value']
                        
                        key_and_oid = format_as_redis_key(formatted_key, oid)
                        redis_store.lpush(temp_ordering_key, key_and_oid)
                        redis_store.set(key_and_oid, "{}|{}".format(dtype, value))

                redis_store.sort(temp_ordering_key, store=formatted_key + '-oids_ordering', alpha=True)
                redis_store.delete(temp_ordering_key)
                redis_store.rpush(asset_key, formatted_key)            

        except StopIteration:
            print('Detected asset that is not supported')

if __name__ == '__main__':
    initialize()
