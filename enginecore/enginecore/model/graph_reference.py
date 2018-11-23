"""DB driver (data-layer) that provides access to db sessions and contains commonly used queries """

import os
from neo4j.v1 import GraphDatabase, basic_auth
from enginecore.state.utils import format_as_redis_key
import enginecore.model.query_helpers as qh

class GraphReference():
    """Graph DB wrapper """
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
            list: parent assets (powering child)
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
                ))

            if record['oid'] and record['oid_details']:
                oid = record['oid'].get('OID')
                oid_rkey = format_as_redis_key(str(asset_key), oid, key_formatted=False)
                oid_keys[oid_rkey] = {v:k for k, v in dict(record['oid_details']).items()} # swap order
                
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
    def get_asset_oid_by_name(cls, session, asset_key, oid_name):
        """Get OID that belongs to a particular asset by human-readable name
        Args:
            session: database session
            asset_key(int): key of the asset OID belongs to
            oid_name(str): OID name
        Returns:
            tuple: str as SNMP OID that belongs to the asset, 
                   followed by an int as datatype, followed by optional state details; 
                   returns None if there's no such OID
        """


        results = session.run( 
            """
            MATCH (:Asset { key: $key })-[:HAS_OID]->(oid {OIDName: $oid_name}) 
            OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(oid_details)
            RETURN oid, oid_details
            """,
            key=asset_key, oid_name=oid_name
        )

        record = results.single()
        details = record.get('oid') if record else None

        oid_info = details['OID'] if details else None

        # get vendor specific information
        v_specs = {v:k for k, v in dict(record['oid_details']).items()} if (record and record['oid_details']) else None
        oid_data_type = details['dataType'] if oid_info else None

        return oid_info, oid_data_type, v_specs


    @classmethod
    def get_component_oid_by_name(cls, session, component_key, oid_name):
        """Get OID that is associated with a particular component (by human-readable name)
        Args:
            session: database session
            component_key(int): key of the component
            oid_name(str): OID name
        Returns:
            tuple: SNMP OID that belongs to the enclosing asset (as str), key of the asset component belongs to (int)
        """


        result = session.run(
            """
            MATCH (component:Component { key: $key})<-[:HAS_COMPONENT]-(p:Asset)-[:HAS_OID]->(oid:OID {OIDName: $name})
            RETURN oid, p.key as parent_key
            """,
            name=oid_name, key=component_key
        )
        record = result.single()

        oid_info = record.get('oid')
        parent_key = record.get('parent_key')
        
        return oid_info['OID'], int(parent_key) if (oid_info and 'OID' in oid_info) else None


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
            MATCH (asset:Asset) 
            OPTIONAL MATCH (asset)-[:HAS_COMPONENT]->(component:Component)
            OPTIONAL MATCH (asset)<-[:POWERED_BY]-(childAsset:Asset) 
            RETURN asset, count(DISTINCT component) as num_components, collect(childAsset) as children 
            ORDER BY asset.key ASC
            """
        )

        assets = list(map(lambda x: dict({
            **x['asset'], 
            'children': x['children'],
            'num_components': x['num_components']
        }), list(results)))

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
                    """
                    MATCH (c:Component)-[:POWERED_BY]->(parent) 
                    WHERE c.key IN $list RETURN parent ORDER BY c.key
                    """"", list=keys
                )

                asset['parent'] = []
                for presult in presults:
                    asset['parent'].append(dict(presult['parent']))

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
            tuple: consisting of 3 (optional) items: 1) child assets that are powered by the updated asset
                                                     2) parent(s) of the updated asset
                                                     3) second parent of the child assets  
        """

        # look up child nodes & parent node
        results = session.run(
            """
            OPTIONAL MATCH  (parentAsset:Asset)<-[:POWERED_BY]-(updatedAsset { key: $key }) 
            OPTIONAL MATCH (nextAsset:Asset)-[:POWERED_BY]->({ key: $key }) 
            OPTIONAL MATCH (nextAsset2ndParent)<-[:POWERED_BY]-(nextAsset) 
            WHERE updatedAsset.key <> nextAsset2ndParent.key 
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
            """
            MATCH (n:Asset { key: $key }) OPTIONAL MATCH (n)-[:HAS_COMPONENT]->(c) 
            RETURN n as asset, labels(n) as labels, collect(c) as children
            """, key=int(asset_key)
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
    def save_layout(cls, session, layout, stage=None):
        """Save system layout (X, Y coordinates of the assets & stage) 

        Args:
            session: database session
            layout(list): list of new x & y positions in the format 'asset_key: { x: new_x, y: new_y }'
            stage(dict): stage properties including x, y and scale
        """
        for k in layout:
            if layout[k]:
                session.run(
                    "MATCH (a:Asset { key: $key }) SET a.x=$x, a.y=$y",
                    key=int(k), x=layout[k]['x'], y=layout[k]['y']
                )
        if stage:
            session.run(
                "MERGE (n:StageLayout { sref: 1 }) SET n.scale=$scale, n.x=$x, n.y=$y",
                scale=stage['scale'], x=stage['x'], y=stage['y']
            )
    

    @classmethod
    def get_stage_layout(cls, session):
        """Get Stage layout configurations

        Args:
            session: database session
        Returns:
            dict: stage coordinates (x,y) & its scale
        """
        results = session.run(
            "MATCH (stageLayout:StageLayout) RETURN stageLayout"
        )

        stage_layout = results.single()

        return dict(stage_layout.get('stageLayout')) if stage_layout else None


    @classmethod
    def get_asset_sensors(cls, session, asset_key):
        """Get sensors that belong to a particular asset
        
        Args:
            session: database session
            asset_key: key of the asset sensors belong to
        Returns:
            list: of sensor dictionaries
        """
        results = session.run(
            """
            MATCH (a:Asset { key: $key })-[:HAS_SENSOR]->(sensor:Sensor)
            OPTIONAL MATCH (sensor)-[:HAS_ADDRESS_SPACE]->(addr)
            RETURN sensor, addr
            """, key=int(asset_key)
        )

        sensors = []

        for record in results:
            sensor = dict(record['sensor'])

            sensors.append({ 
                'specs': sensor, 
                'address_space': dict(record['addr']) if 'index' in sensor else None
            })

        return sensors

    
    @classmethod
    def get_mains_powered_outlets(cls, session):
        """Wall-powered outlets

        Args:
            session: database session
        Returns:
            list: of outlet keys powered by the mains
        """
        results = session.run(
            """
            MATCH (outlet:Outlet) WHERE NOT (outlet)-[:POWERED_BY]->(:Asset) RETURN outlet.key as key
            """
        )
        # print(results['key'])
        return list(map(lambda x: x.get('key'), results))
            

    @classmethod
    def get_affected_sensors(cls, session, server_key, source_name):
        """Get sensors affected by the source sensor
        
        Args:
            session: database session
            server_key(int): key of the server sensors belong to
            source_name(str): name of the source sensor
        Returns:
            dict: source and target sensor details    
        """
        
        results = session.run(
            """
            MATCH (:ServerWithBMC { key: $server })-[:HAS_SENSOR]->(source:Sensor { name: $source })
            MATCH (source)<-[rel]-(targets:Sensor) return source, targets, collect(rel) as rel
            """,
            server=server_key,
            source=source_name
        )

        thermal_details = {'source': {}, 'targets': [],}

        for record in results:
            thermal_details['source'] = dict(record.get('source'))
             
            thermal_details['targets'].append(
                {**dict(record.get('targets')), **{"rel": list(map(dict, record.get('rel')))}}
            )

        # print(source_name, thermal_details)

        return thermal_details


    @classmethod
    def get_sensor_thermal_rel(cls, session, server_key, relationship):
        """Get thermal details about target sensor affected by the source sensor
        Args:
            session: database session
            server_key(int): key of the server sensors belong to
            relationship(dict): source, target and event 
        """

        results = session.run(
            """
            MATCH (:ServerWithBMC { key: $server })-[:HAS_SENSOR]->(source:Sensor { name: $source })
            MATCH (source)<-[rel]-(target:Sensor {name: $target})
            WHERE rel.event = $event
            RETURN source, target, rel
            """, 
            server=server_key,
            source=relationship['source'],
            target=relationship['target'],
            event=relationship['event']
        )

        record = results.single()
        return {
            'source': dict(record.get('source')), 
            'target': dict(record.get('target')), 
            'rel': dict(record.get('rel')) 
        } if record else None


    @classmethod
    def get_cpu_thermal_rel(cls, session, server_key, sensor_name):
        """Get thermal relationships between CPU and a sensor 
        Args:
            session:  database session
            server_key(int): key of the server sensors belong to
            sensor_name(str): name of the sensor affected by CPU load
        """

        results = session.run(
            """
            MATCH (:ServerWithBMC { key: $server })-[:HAS_SENSOR]->(sensor:Sensor { name: $sensor })
            MATCH (:CPU)<-[rel:HEATED_BY]-(sensor)
            RETURN rel
            """,
            server=server_key,
            sensor=sensor_name
        )

        record = results.single()
        return dict(record.get('rel')) if record else None


    @classmethod
    def get_ambient_props(cls, session):
        """Get properties belonging to ambient """
        
        results = session.run(
            "MATCH (sys:SystemEnvironment)-[:HAS_PROP]->(props:EnvProp) RETURN props"
        )

        amp_props = {}

        for record in results:
            event_prop = dict(record.get('props'))
            amp_props[event_prop['event']] = event_prop

        return amp_props 


    @classmethod
    def set_ambient_props(cls, session, properties):
        """Save ambient properties """

        query = []
        s_attr = ['event', 'degrees', 'rate', 'pause_at', 'sref']

        query.append('MERGE (sys:SystemEnvironment { sref: 1 })')
        query.append('MERGE (sys)-[:HAS_PROP]->(env:EnvProp {{ event: "{}" }})'.format(properties['event']))

        set_stm = qh.get_set_stm(properties, node_name="env", supported_attr=s_attr)
        query.append('SET {}'.format(set_stm))

        session.run("\n".join(query))
