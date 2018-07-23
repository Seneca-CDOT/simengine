import os
from neo4j.v1 import GraphDatabase, basic_auth
from enginecore.state.utils import format_as_redis_key

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
    def get_parent_assets(cls, session, asset_key):
        """Get information about parent assets

        Args:
            session: database session
            asset_key(int): key of the *child asset
        Returns:
        """
        results = session.run(
            "MATCH (:Asset { key: $key })-[:POWERED_BY]->(asset:Asset) RETURN asset",
            key=int(asset_key)
        )

        assets = list(map(lambda x: dict(x['asset']), list(results)))
        return assets

    @classmethod
    def get_parent_keys(cls, session, asset_key):
        """Get keys of parent assets/OIDs that power node with the supplied key
        Node is only affected by *its own OIDs or assets up the power chain

        Args:
            session: database session
            asset_key(int): key of the affected node
        Returns:
            tuple: parent asset keys & parent OIDs with state specs that directly affect the node (formatted for Redis)
        """
        results = session.run(
            """
            MATCH (a:Asset { key: $key })-[:POWERED_BY]->(parent:Asset) 
            OPTIONAL MATCH (a:Asset { key: $key })-[:POWERED_BY]->(oid:OID)<-[:HAS_OID]-(parent:Asset)
            OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(oid_details) RETURN parent, oid, oid_details
            """,
            key=int(asset_key)
        )

        asset_keys = []
        oid_keys = {}
        for record in results:
            
            asset_type = record['parent']['type']
            
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
    def get_asset_oid_info(cls, session, asset_key, oid):
        """Get oid info & (state) details that belong to a particular asset
        Args:
            session: database session
            asset_key(int): query asset by key
            oid(str): object id that belongs to the asset
        Returns:
            tuple: list of assets powered by the OID and OID specs
        """

        results = session.run(
            """
            MATCH (asset:Asset)-[:POWERED_BY]->(oid:OID { OID: $oid })<-[:HAS_OID]-({key: $key}) 
            MATCH (oid)-[:HAS_STATE_DETAILS]->(oid_specs)
            RETURN asset, oid, oid_specs
            """, oid=oid, key=asset_key
        )

        keys_oid_powers = []
        oid_specs = {}
        for record in results:
            keys_oid_powers.append(record['asset'].get('key'))
            oid_specs = {
                'name': record['oid']['OIDName'],
                'specs': dict(record['oid_specs'])
            }
        
        return keys_oid_powers, oid_specs

    @classmethod
    def get_assets_and_children(cls, session):
        """Get assets and children that are powered by them
        
        Args:
            session: database session
        Returns:
            list: list of assets ordered by key (ascending) & its child asset(s) 
        """

        results = session.run(
            """
            MATCH (asset:Asset) OPTIONAL MATCH (asset)<-[:POWERED_BY]-(childAsset:Asset) 
            RETURN asset, collect(childAsset) as children ORDER BY asset.key ASC
            """
        )

        assets = list(map(lambda x: dict({**x['asset'], 'children': x['children']}), list(results)))
        return assets
            
    @classmethod
    def get_assets_and_connections(cls, session, flatten=True):
        """Get assets, their components (e.g. PDU outlets) and parent asset(s) that powers them

        Args:
            session: database session
            flatten(bool): if false, assets' children will nested under 'children' key
        Returns:
            list: list of asset details with it's 'parent' & 'children' information
        """

        results = session.run(
            """
            MATCH (asset:Asset) WHERE NOT (asset)<-[:HAS_COMPONENT]-(:Asset)
            OPTIONAL MATCH (asset)-[:POWERED_BY]->(p:Asset)
            OPTIONAL MATCH (asset)-[:HAS_COMPONENT]->(c) 
            RETURN asset, collect(DISTINCT c) as children,  collect(DISTINCT p) as parent
            """
        )

        assets = {}
        for record in results:
            
            asset = dict(record['asset'])
            
            ## Set asset parent(s)
            asset['parent'] = list(map(dict, list(record['parent']))) if record['parent'] else None

            # For server type, parent will not be a PSU but an asset that powers that PSU
            if (asset['type'] == 'server' or asset['type'] == 'serverwithbmc') and asset['parent']:
                keys = map(lambda x: x['key'], asset['parent'])
                presults = session.run(
                    "MATCH (c:Component)-[:POWERED_BY]->(parent) WHERE c.key IN $list RETURN parent", list=keys
                )

                asset['parent'] = []
                for r in presults:
                    asset['parent'].append(dict(r['parent']))

            ## Set asset children 
            # format asset children as list of child_key: { child_info }
            if record['children']:
                nested_assets = {c['key']: {**dict(c), 'type': c['type']} for c in record['children']}
                if flatten:
                    asset['children'] = sorted(list(map(lambda x: x['key'], record['children'])))
                    assets = {**assets, **nested_assets} # merge dicts
                else:
                    asset['children'] = nested_assets

            assets[record['asset'].get('key')] = asset
  
        return assets
    
    
    @classmethod
    def get_affected_assets(cls, session, asset_key):
        """Get information about assets affected by a change in parent's state

        Args:
            session: database session
            asset_key(int): key of the updated asset
        
        Returns:

        """

        # look up child nodes & parent node
        results = session.run(
            """
            OPTIONAL MATCH  (parentAsset:Asset)<-[:POWERED_BY]-(updatedAsset { key: $key }) 
            OPTIONAL MATCH (nextAsset:Asset)-[:POWERED_BY]->({ key: $key }) 
            OPTIONAL MATCH (nextAsset2ndParent)<-[:POWERED_BY]-(nextAsset) WHERE updatedAsset.key <> nextAsset2ndParent.key 
            RETURN collect(nextAsset) as childAssets, collect(parentAsset) as parentAsset, nextAsset2ndParent
            """,
            key=asset_key
        )

        list_of_dicts = lambda r: list(map(dict, list(r)))

        record = results.single()
        return (
            list_of_dicts(record['childAssets']) if record['childAssets'] else list(),
            list_of_dicts(record['parentAsset']) if record['parentAsset'] else list(),
            dict(record['nextAsset2ndParent']) if record['nextAsset2ndParent'] else None
        ) 

  
    @classmethod
    def get_asset_and_components(cls, session, asset_key):
        """Get information about individual asset & its components 
        Component may be a PSU that belongs to a server or PDU outlets

        Args:
            session: database session
            asset_key(int): query by key
        
        Returns:
            dict: asset details with it's 'labels' and components as 'children' (sorted by key) 
        """
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
    def get_asset_labels(cls, session, asset_key):        
        """Retrieve asset labels 

        Args:
            session: database session
            asset_key(int): query by key
        Returns:
            list: list of asset labels
        """

        results = session.run(
            "MATCH (a:Asset { key: $key }) RETURN labels(a) as labels LIMIT 1",
            key=int(asset_key)
        )

        return results.single()['labels']

    @classmethod
    def save_layout(cls, session, layout):
        """Save system layout (X, Y positions) 

        Args:
            session: database session
            layout(list): list of new x & y positions in the format 'asset_key: { x: new_x, y: new_y }'
        """
        for k in layout:
            if layout[k]:
                session.run(
                    "MATCH (a:Asset { key: $key }) SET a.x=$x, a.y=$y",
                    key=int(k), x=layout[k]['x'], y=layout[k]['y']
                )
            
