from neo4j.v1 import GraphDatabase, basic_auth
import signal
import sys
import os

from enginecore.state.utils import format_as_redis_key
import enginecore.state.assets

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GraphReference(metaclass=Singleton):
    
    
    def __init__(self):
        self._driver = GraphDatabase.driver(
            'bolt://localhost', 
            auth=basic_auth(os.environ.get('NEO4J_USR', 'test'), os.environ.get('NEO4J_PSW', 'test'))
        )

    
    def close(self):
        """ Close as db """
        self._driver.close()


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
            tuple: parent asset keys & parent OIDs that directly affect the node (formatted for Redis)
        """
        results = session.run(
            "MATCH (a:Asset { key: $key })-[:POWERED_BY*]->(parent:Asset) RETURN parent, null as oid \
            UNION \
            MATCH (a:Asset { key: $key })-[:POWERED_BY]->(oid:OID)<-[:HAS_OID]-(parent:Asset) RETURN parent, oid",
            key=int(key)
        )

        asset_keys = []
        oid_keys = []
        for record in results:
            
            asset_label = set(enginecore.state.assets.SUPPORTED_ASSETS).intersection(
                map(lambda x: x.lower(), record['parent'].labels)
            )
            
            asset_key = record['parent'].get('key')
            if not record['oid']:
                asset_label = next(iter(asset_label))
                asset_keys.append("{asset_key}-{property}".format(
                    asset_key=asset_key, 
                    property=asset_label.lower()
                    )
                )
            else:
                oid = record['oid'].get('OID')
                oid_keys.append(format_as_redis_key(str(asset_key), oid, key_formatted=False))

        return asset_keys, oid_keys


    @classmethod
    def get_assets(cls, session):
        """"""
        results = session.run(
            "MATCH (asset:Asset) OPTIONAL MATCH (asset)-[:HAS_SNMP_COMPONENT]->(c) return asset, collect(c) as children"
        )

        assets = {}
        for record in results:
            
            asset = { 'key': record['asset'].get('key') }
            asset_label = set(enginecore.state.assets.SUPPORTED_ASSETS).intersection(
                map(lambda x: x.lower(), record['asset'].labels)
            )

            asset['type'] = next(iter(asset_label))

            if record['children']:
                # TODO: sort with neo4j
                asset['children'] = sorted(list(map(lambda x: x['key'], record['children'])))

            assets[record['asset'].get('key')] = asset

        return assets
    

    @classmethod
    def get_asset_and_components(cls, session, asset_key):
        results = session.run(
            "MATCH (n:Asset { key: $key }) OPTIONAL MATCH (n)-[:HAS_SNMP_COMPONENT]->(c) RETURN n as asset, collect(c) as children",
            key=asset_key
        )

        record = results.single()
        
        asset_label = set(enginecore.state.assets.SUPPORTED_ASSETS).intersection(
            map(lambda x: x.lower(), record['asset'].labels)
        )

        asset_key = record['asset'].get('key')
        children = []

        if record['children']:
            children = sorted(list(map(lambda x: x['key'], record['children'])))
            
        return {
            'type': next(iter(asset_label)),
            'children': children,
            'key': asset_key
        }
        

    @classmethod
    def get_node_by_key(cls, session, key):
        results = session.run(
            "MATCH (a:Asset { key: $key }) RETURN labels(a) as labels LIMIT 1",
            key=int(key)
        )

        return results.single()['labels']
