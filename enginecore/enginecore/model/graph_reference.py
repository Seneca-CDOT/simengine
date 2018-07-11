import os
from neo4j.v1 import GraphDatabase, basic_auth
from enginecore.state.utils import format_as_redis_key, get_asset_type

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GraphReference():
    
    
    def __init__(self):
        self._driver = GraphDatabase.driver(
            'bolt://localhost', 
            auth=basic_auth(os.environ.get('NEO4J_USR', 'simengine'), os.environ.get('NEO4J_PSW', 'simengine'))
        )

    
    def close(self):
        """ Close as db """
        # self._driver.close()


    def get_session(self):
        """ Get a database session """
        return self._driver.session()


    @classmethod
    def get_parent_keys(cls, session, key):
        """ Get keys of parent assets/OIDs that power node with the supplied key
        Node is only affected by *its own OIDs or assets up the power chain

        Args:
            session: database session
            key(int): key of the affected node
        Returns:
            tuple: parent asset keys & parent OIDs with state specs that directly affect the node (formatted for Redis)
        """
        results = session.run(
            "MATCH (a:Asset { key: $key })-[:POWERED_BY]->(parent:Asset) \
            OPTIONAL MATCH (a:Asset { key: $key })-[:POWERED_BY]->(oid:OID)<-[:HAS_OID]-(parent:Asset)\
            OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(oid_details) RETURN parent, oid, oid_details",
            key=int(key)
        )

        asset_keys = []
        oid_keys = {}
        for record in results:
            
            asset_type = get_asset_type(record['parent'].labels)
            
            asset_key = record['parent'].get('key')           
            asset_keys.append("{asset_key}-{property}".format(
                asset_key=asset_key, 
                property=asset_type.lower()
                )
            )

            if record['oid'] and record['oid_details']:
                oid = record['oid'].get('OID')
                oid_rkey = format_as_redis_key(str(asset_key), oid, key_formatted=False)
                oid_keys[oid_rkey] = {v:k for k,v in dict(record['oid_details']).items()} # swap order
                
        return asset_keys, oid_keys


    @classmethod
    def get_assets(cls, session, flatten=True):
        """ Get assets, their components (e.g. PDU outlets) and parent asset that powers them """

        results = session.run(
            "MATCH (asset:Asset) WHERE NOT (asset)<-[:HAS_COMPONENT]-(:Asset)\
            OPTIONAL MATCH (asset)-[:POWERED_BY]->(p:Asset)\
            OPTIONAL MATCH (asset)-[:HAS_COMPONENT]->(c) return asset, collect(DISTINCT c) as children,  collect(DISTINCT p) as parent"
        )

        assets = {}
        for record in results:
            
            asset = dict(record['asset'])
            asset['type'] = get_asset_type(record['asset'].labels)
            asset['parent'] = list(map(dict, list(record['parent']))) if record['parent'] else None

            if asset['type'] == 'server' and asset['parent']:
                keys = map(lambda x: x['key'], asset['parent'])
                presults = session.run(
                    "MATCH (c:Component)-[:POWERED_BY]->(parent) WHERE c.key IN $list RETURN parent", list=keys
                )

                asset['parent'] = []
                for r in presults:
                    asset['parent'].append(dict(r['parent']))



            if record['children']:
                nested_assets = {c['key']: {**dict(c), 'type': get_asset_type(c.labels)} for c in record['children']}
                if flatten:
                    asset['children'] = sorted(list(map(lambda x: x['key'], record['children'])))
                    assets = {**assets, **nested_assets} # merge dicts
                else:
                    asset['children'] = nested_assets

            assets[record['asset'].get('key')] = asset
  
        return assets
    

    @classmethod
    def get_asset_and_components(cls, session, asset_key):
        results = session.run(
            "MATCH (n:Asset { key: $key }) OPTIONAL MATCH (n)-[:HAS_COMPONENT]->(c) RETURN n as asset, labels(n) as labels, collect(c) as children",
            key=int(asset_key)
        )

        record = results.single()
        asset = dict(record['asset'])
        asset['labels'] = record['labels']

        children = []
        if record['children']:
            children = sorted(list(map(lambda x: x['key'], record['children'])))
        
        asset['children'] = children
        return asset

    @classmethod
    def get_asset_labels_by_key(cls, session, key):
        results = session.run(
            "MATCH (a:Asset { key: $key }) RETURN labels(a) as labels LIMIT 1",
            key=int(key)
        )

        return results.single()['labels']

    @classmethod
    def save_layout(cls, session, data):
        """ Save system layout """
        print(data)
        for k in data:
            if data[k]:
                session.run(
                    "MATCH (a:Asset { key: $key }) SET a.x=$x, a.y=$y",
                    key=int(k), x=data[k]['x'], y=data[k]['y']
                )
            
