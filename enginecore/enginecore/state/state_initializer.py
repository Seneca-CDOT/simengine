""" Initialize redis state based on reference model """
import redis

from neo4j.v1 import GraphDatabase, basic_auth
from state.asset_types import ASSET_TYPES
from state.graph_reference import get_db

def initialize():
    graph_db = get_db()
    redis_store = redis.StrictRedis(host='localhost', port=6379)
    
    results = graph_db.run(
        "MATCH (asset:Asset) OPTIONAL MATCH (asset:Asset)-[:HAS_OID]->(oid)"
        "return asset, collect(oid) as oids"
    )

    supports_asset = lambda x: x.lower() if x.lower() in ASSET_TYPES else None

    for record in results:
        asset_types = filter(supports_asset, record['asset'].labels)
        asset_key = str(record['asset'].get('key'))

        for asset_type in asset_types:
            redis_store.set("{}-{}".format(asset_key, asset_type.lower()), "1") # TODO: default state in graph db 

        for oid in record['oids']: # loop over oids that are defined in the graph db

            oid_digits = oid.get('OID').split('.')
            
            # if oid_digits[0] == '.':
            oid_digits.pop(0)

            formated_key = asset_key.zfill(10) + '-'
            
            for digit in oid_digits[:-1]:
                formated_key += (digit + '.').rjust(11, ' ')
            formated_key += (oid_digits[-1]).rjust(10, ' ')

            redis_store.set(formated_key, "65|" + str(oid.get('defaultValue'))) # testing

if __name__ == '__main__':
    initialize()
