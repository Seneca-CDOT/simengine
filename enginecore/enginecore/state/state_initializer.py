""" Initialize redis state based on reference model """
import redis

from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.graph_reference import GraphReference

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
            redis_store.set("{}-{}".format(asset_key, next(iter(asset_label),'').lower()), "1") # TODO: default state in graph db 

            for oid in record['oids']: # loop over oids that are defined in the graph db
 
                oid_digits = oid.get('OID').split('.')
                
                # if oid_digits[0] == '.':
                oid_digits.pop(0)

                formated_key = asset_key.zfill(10) + '-'
                
                for digit in oid_digits[:-1]:
                    formated_key += (digit + '.').rjust(11, ' ')
                formated_key += (oid_digits[-1]).rjust(10, ' ')

                redis_store.set(formated_key, "65|" + str(oid.get('defaultValue'))) # testing
        except KeyError:
            print('Detected asset that is not supported')

if __name__ == '__main__':
    initialize()
