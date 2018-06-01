from neo4j.v1 import GraphDatabase, basic_auth
import signal
import sys


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GraphReference(metaclass=Singleton):
    
    
    def __init__(self):
        self._driver = GraphDatabase.driver('bolt://localhost', auth=basic_auth("test", "test"))

    
    def close(self):
        self._driver.close()


    def get_session(self):
        return self._driver.session()


    @classmethod
    def get_parent_keys(cls, session, key):
        """ Get keys of parent assets/OIDs that power node with the supplied key
        Node is only affected by *its own OIDs or assets up the power chain

        Args:
            session: database session
            key(int): key of the affected node
        Returns:
            list: list of parent nodes that power up the asset
        """
        results = session.run(
            "MATCH (a:Asset { key: $key })-[:POWERED_BY*]->(parent:Asset) RETURN parent \
            UNION \
            MATCH (a:Asset { key: $key })-[:POWERED_BY]->(parent:OID) RETURN parent",
            key=key
        )

        keys = []
        for record in results:
            keys.append(record['parent'].get('key'))

        return keys


    @classmethod
    def get_node_by_key(cls, session, key):
        results = session.run(
            "MATCH (a:Asset { key: $key }) RETURN labels(a) as labels LIMIT 1",
            key=int(key)
        )

        return results.single()['labels']
