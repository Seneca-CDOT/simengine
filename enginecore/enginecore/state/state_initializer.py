""" Initialize redis state based on reference model """
import redis

from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.graph_reference import GraphReference
from enginecore.state.utils import format_as_redis_key

def initialize():
    graph_ref = GraphReference()
    redis_store = redis.StrictRedis(host='localhost', port=6379)

    results = graph_ref.get_session().run(
        "MATCH (asset:Asset) OPTIONAL MATCH (asset:Asset)-[:HAS_OID]->(oid)"
        "return asset, collect(oid) as oids"
    )

    for record in results:
        try:
            asset_label = set(SUPPORTED_ASSETS).intersection(
                map(lambda x: x.lower(), record['asset'].labels)
            )

            asset_key = str(record['asset'].get('key'))
            redis_store.set("{}-{}".format(asset_key, next(iter(asset_label),'').lower()), "1")

            formatted_key = asset_key.zfill(10)

            for oid in record['oids']: # loop over oids that are defined in the graph db
                 
                key_and_oid = format_as_redis_key(formatted_key, oid.get('OID'))

                redis_store.lpush(formatted_key + "-temp_oids_ordering", key_and_oid)
                redis_store.set(key_and_oid, "{}|{}".format(oid.get('dataType'), oid.get('defaultValue'))) 
     
            if 'SNMPSim' in record['asset'].labels and record['oids']:
                redis_store.sort(formatted_key + 'temp_oids_ordering', store=formatted_key + '-oids_ordering', alpha=True)
                redis_store.delete(formatted_key + '-' + 'temp_oids_ordering')
                redis_store.rpush(asset_key, formatted_key)            

        except KeyError:
            print('Detected asset that is not supported')

if __name__ == '__main__':
    initialize()
