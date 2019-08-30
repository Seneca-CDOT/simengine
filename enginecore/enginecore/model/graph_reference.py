"""DB driver (data-layer) that provides access
to db sessions and contains commonly used queries """

# Minimizing Cypher queries lengths is just too tedious
# (black formatter will handle most cases):
# pylint: disable=line-too-long

import os
import json
import time
from enum import Enum

from neo4j.v1 import GraphDatabase, basic_auth
from enginecore.tools.utils import format_as_redis_key
import enginecore.tools.query_helpers as qh


class GraphReference:
    """Graph DB wrapper """

    def __init__(self):
        self._driver = GraphDatabase.driver(
            "bolt://localhost",
            auth=basic_auth(
                os.environ.get("NEO4J_USR", "simengine"),
                os.environ.get("NEO4J_PSW", "simengine"),
            ),
        )

    def close(self):
        """ Close as db """
        self._driver.close()

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
            key=int(asset_key),
        )

        assets = list(map(lambda x: dict(x["asset"]), list(results)))
        return assets

    @classmethod
    def get_parent_keys(cls, session, asset_key):
        """Get keys of parent assets/OIDs that power node with the supplied key
        Node is only affected by *its own OIDs or assets up the power chain

        Args:
            session: database session
            asset_key(int): key of the affected node
        Returns:
            tuple: parent asset keys & parent OIDs with state specs that 
                   directly affect the node (formatted for Redis)
        """
        results = session.run(
            """
            MATCH (a:Asset { key: $key })-[:POWERED_BY]->(parent:Asset) 
            OPTIONAL MATCH (a:Asset { key: $key })-[:POWERED_BY]->(oid:OID)<-[:HAS_OID]-(parent:Asset)
            OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(oid_details) RETURN parent, oid, oid_details
            """,
            key=int(asset_key),
        )

        asset_keys = []
        oid_keys = {}
        for record in results:
            asset_key = record["parent"].get("key")
            asset_keys.append(asset_key)

            if record["oid"] and record["oid_details"]:
                oid = record["oid"].get("OID")
                oid_rkey = format_as_redis_key(str(asset_key), oid, key_formatted=False)
                oid_keys[oid_rkey] = {
                    v: k for k, v in dict(record["oid_details"]).items()
                }  # swap order

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
            """,
            oid=oid,
            key=asset_key,
        )

        keys_oid_powers = []
        oid_specs = {}

        record = results.single()

        asset_key = record["asset"].get("key")
        oid_specs = {
            "name": record["oid"]["OIDName"],
            "specs": dict(record["oid_specs"]),
        }

        return asset_key, oid_specs

    @classmethod
    def get_asset_oid_by_name(cls, session, asset_key, oid_name):
        """Get OID that belongs to a particular asset by human-readable name
        Args:
            session: database session
            asset_key(int): key of the asset OID belongs to
            oid_name(str): OID name
        Returns:
            tuple: str as SNMP OID that belongs to the asset, 
                   followed by optional state details; 
                   returns None if there's no such OID
        """

        results = session.run(
            """
            MATCH (:Asset { key: $key })-[:HAS_OID]->(oid {OIDName: $oid_name}) 
            OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(oid_details)
            RETURN oid, oid_details
            """,
            key=asset_key,
            oid_name=oid_name,
        )

        record = results.single()
        details = record.get("oid") if record else None

        oid_info = details["OID"] if details else None

        # get vendor specific information
        v_specs = (
            {v: k for k, v in dict(record["oid_details"]).items()}
            if (record and record["oid_details"])
            else None
        )

        return oid_info, v_specs

    @classmethod
    def get_component_oid_by_name(cls, session, component_key, oid_name):
        """Get OID that is associated with a particular component
        (by human-readable name)

        Args:
            session: database session
            component_key(int): key of the component
            oid_name(str): OID name
        Returns:
            tuple: SNMP OID that belongs to the enclosing asset (as str);
                   key of the asset component belongs to (int)
        """

        result = session.run(
            """
            MATCH (component:Component { key: $key})<-[:HAS_COMPONENT]-(p:Asset)-[:HAS_OID]->(oid:OID {OIDName: $name})
            RETURN oid, p.key as parent_key
            """,
            name=oid_name,
            key=component_key,
        )
        record = result.single()

        oid_info = record.get("oid")
        parent_key = record.get("parent_key")

        return (
            oid_info["OID"],
            int(parent_key) if (oid_info and "OID" in oid_info) else None,
        )

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
            RETURN asset, count(DISTINCT component) as num_components,
                   collect(childAsset) as children 
            ORDER BY asset.key ASC
            """
        )

        assets = list(
            map(
                lambda x: dict(
                    {
                        **x["asset"],
                        "children": x["children"],
                        "num_components": x["num_components"],
                    }
                ),
                list(results),
            )
        )

        return assets

    @classmethod
    def get_assets_and_connections(cls, session, flatten=True):
        """Get assets, their components (e.g. PDU outlets)
        and parent asset(s) that powers them

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
            RETURN asset, collect(DISTINCT c) as children, 
            collect(DISTINCT p) as parent
            """
        )

        assets = {}
        for record in results:

            asset = dict(record["asset"])

            ## Set asset parent(s)
            asset["parent"] = (
                list(map(dict, list(record["parent"]))) if record["parent"] else None
            )

            # For server type, parent will not be a PSU but an asset that powers that PSU
            if (
                asset["type"] == "server" or asset["type"] == "serverwithbmc"
            ) and asset["parent"]:
                keys = map(lambda x: x["key"], asset["parent"])
                presults = session.run(
                    """
                    MATCH (c:Component)-[:POWERED_BY]->(parent) 
                    WHERE c.key IN $list RETURN parent ORDER BY c.key
                    """
                    "",
                    list=keys,
                )

                asset["parent"] = []
                for presult in presults:
                    asset["parent"].append(dict(presult["parent"]))

            ## Set asset children
            # format asset children as list of child_key: { child_info }
            if record["children"]:
                nested_assets = {
                    c["key"]: {**dict(c), "type": c["type"]} for c in record["children"]
                }
                if flatten:
                    asset["children"] = sorted(
                        list(map(lambda x: x["key"], record["children"]))
                    )
                    assets = {**assets, **nested_assets}  # merge dicts
                else:
                    asset["children"] = nested_assets

            assets[record["asset"].get("key")] = asset

        return assets

    @classmethod
    def get_affected_assets(cls, session, asset_key):
        """Get information about assets affected by a change in parent's state

        Args:
            session: database session
            asset_key(int): key of the updated asset
        
        Returns:
            tuple: consisting of 3 (optional) items:
                    1) child assets that are powered by the updated asset
                    2) parent(s) of the updated asset
                    3) second parent of the child assets
        """

        # look up child nodes & parent node
        results = session.run(
            """
            OPTIONAL MATCH (parentAsset:Asset)<-[:POWERED_BY]-(updatedAsset { key: $key }) 
            OPTIONAL MATCH (nextAsset:Asset)-[:POWERED_BY]->({ key: $key }) 
            OPTIONAL MATCH (nextAsset2ndParent)<-[:POWERED_BY]-(nextAsset) 
            WHERE updatedAsset.key <> nextAsset2ndParent.key 
            RETURN collect(nextAsset) as childAssets,
                   collect(distinct parentAsset) as parentAsset, nextAsset2ndParent
            """,
            key=asset_key,
        )

        list_of_dicts = lambda r: list(map(dict, list(r)))

        record = results.single()
        return (
            list_of_dicts(record["childAssets"]) if record["childAssets"] else list(),
            list_of_dicts(record["parentAsset"]) if record["parentAsset"] else list(),
            dict(record["nextAsset2ndParent"])
            if record["nextAsset2ndParent"]
            else None,
        )

    @classmethod
    def get_asset_and_components(cls, session, asset_key):
        """Get information about individual asset & its components 
        Component may be a PSU that belongs to a server or PDU outlets

        Args:
            session: database session
            asset_key(int): query by key
        
        Returns:
            dict: asset details with it's 'labels' 
                  and components as 'children' (sorted by key) 
        """
        results = session.run(
            """
            MATCH (n:Asset { key: $key }) OPTIONAL MATCH (n)-[:HAS_COMPONENT]->(c) 
            RETURN n as asset, labels(n) as labels, collect(c) as children
            """,
            key=int(asset_key),
        )

        record = results.single()

        if not record:
            return None

        asset = dict(record["asset"])
        asset["labels"] = record["labels"]

        children = []
        if record["children"]:
            children = sorted(list(map(lambda x: x["key"], record["children"])))

        asset["children"] = children
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
                    key=int(k),
                    x=layout[k]["x"],
                    y=layout[k]["y"],
                )
        if stage:
            session.run(
                "MERGE (n:StageLayout { sref: 1 }) SET n.scale=$scale, n.x=$x, n.y=$y",
                scale=stage["scale"],
                x=stage["x"],
                y=stage["y"],
            )

    @classmethod
    def get_stage_layout(cls, session):
        """Get Stage layout configurations

        Args:
            session: database session
        Returns:
            dict: stage coordinates (x,y) & its scale
        """
        results = session.run("MATCH (stageLayout:StageLayout) RETURN stageLayout")

        stage_layout = results.single()

        return dict(stage_layout.get("stageLayout")) if stage_layout else None

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
            """,
            key=int(asset_key),
        )

        sensors = []

        for record in results:
            sensor = dict(record["sensor"])

            sensors.append(
                {
                    "specs": sensor,
                    "address_space": dict(record["addr"])
                    if "index" in sensor
                    else None,
                }
            )

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
        return list(map(lambda x: x.get("key"), results))

    @classmethod
    def format_target_elements(cls, results, t_format=None):
        """Format neo4j results as target sensors"""
        thermal_details = {"source": {}, "targets": []}

        for record in results:
            thermal_details["source"] = dict(record.get("source"))

            if not t_format:
                t_format = lambda r: {
                    **dict(r.get("targets")),
                    **{"rel": list(map(dict, r.get("rel")))},
                }
            thermal_details["targets"].append(t_format(record))

        return thermal_details

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
            source=source_name,
        )

        return cls.format_target_elements(results)

    @classmethod
    def get_affected_hd_elements(cls, session, server_key, source_name):
        """Get storage components affected by the source sensor
        Args:
            session: database session
            server_key(int): key of the server sensor & hd elements belong to
            source_name(str): name of the source sensor
        Returns:
            dict: source and target details
        """

        results = session.run(
            """
            MATCH (:ServerWithBMC { key: $server })-[:HAS_SENSOR]->(source:Sensor { name: $source })
            MATCH (source)<-[rel]-(targets)
            MATCH (controller)-[:HAS_CACHEVAULT|:HAS_PHYSICAL_DRIVE]->(targets)
            WHERE targets:PhysicalDrive or targets:CacheVault
            return source, targets, collect(rel) as rel, controller
            """,
            server=server_key,
            source=source_name,
        )

        output_format = lambda r: {
            **dict(r.get("targets")),
            **{"rel": list(map(dict, r.get("rel")))},
            **{"controller": dict(r.get("controller"))},
        }
        return cls.format_target_elements(results, t_format=output_format)

    @classmethod
    def get_sensor_thermal_rel(cls, session, server_key, relationship):
        """Get thermal details about thermal relationship
        Args:e
            session: database session
            server_key(int): key of the server sensor(s) belong to
            relationship(dict): source, target and event 
        """

        query = []
        query.append(
            'MATCH (:ServerWithBMC {{ key: {} }})-[:HAS_SENSOR]->(source:Sensor {{ name: "{}" }})'.format(
                server_key, relationship["source"]
            )
        )

        query.append(
            "MATCH (source)<-[rel :COOLED_BY|:HEATED_BY]-(target {{ {}: {} }})".format(
                relationship["target"]["attribute"], relationship["target"]["value"]
            )
        )

        query.extend(
            [
                'WHERE rel.event = "{}"'.format(relationship["event"]),
                "RETURN source, target, rel",
            ]
        )

        results = session.run("\n".join(query))
        record = results.single()
        return (
            {
                "source": dict(record.get("source")),
                "target": dict(record.get("target")),
                "rel": dict(record.get("rel")),
            }
            if record
            else None
        )

    @classmethod
    def get_cpu_thermal_rel(cls, session, server_key, sensor_name):
        """Get thermal relationships between CPU and a sensor 
        Args:
            session:  database session
            server_key(int): key of the server sensor belongs to
            sensor_name(str): name of the sensor affected by CPU load
        """

        results = session.run(
            """
            MATCH (:ServerWithBMC { key: $server })-[:HAS_SENSOR]->(sensor:Sensor { name: $sensor })
            MATCH (:CPU)<-[rel:HEATED_BY]-(sensor)
            RETURN rel
            """,
            server=server_key,
            sensor=sensor_name,
        )

        record = results.single()
        return dict(record.get("rel")) if record else None

    @classmethod
    def get_ambient_props(cls, session):
        """Get ambient properties of system environment
        Args:
            session: Graph Database session
        Returns:
            dict: ambient properties and  events'
        """
        return cls._get_sys_env_props(session, cls.SysEnvProperty.ambient)

    @classmethod
    def set_ambient_props(cls, session, properties):
        """Save ambient properties """
        s_attr_prop = ["event", "degrees", "rate", "pause_at", "sref"]
        cls._set_sys_env_props(
            session, properties, s_attr_prop, env_prop_type=cls.SysEnvProperty.ambient
        )

    @classmethod
    def get_voltage_props(cls, session):
        """Get voltage properties of system environment
        Args:
            session: Graph Database session
        Returns:
            dict: voltage fluctuation settings
        """

        return cls._get_sys_env_props(session, cls.SysEnvProperty.voltage)

    class SysEnvProperty(Enum):
        """Supported system environment properties"""

        ambient = 1  # room temperature
        voltage = 2  # the mains voltage

    @classmethod
    def _get_sys_env_props(cls, session, env_prop_type: SysEnvProperty) -> dict:
        """Get ambient properties of system environment
        Args:
            session: Graph Database session
            env_prop_type: System Environment property
        Returns:
            sys environment properties and corresponding events' (if supported)
            None if SysEnv is not initialized yet 
        """

        query = []
        query.append("MATCH (sys:SystemEnvironment { sref: 1 })")
        query.append(
            'MATCH (sys)-[:HAS_PROP]->(env_prop:EnvProp {{ name: "{}" }})'.format(
                env_prop_type.name
            )
        )

        query.append("OPTIONAL MATCH (env_prop)-[:HAS_PROP]->(event:EnvProp )")

        query.append("RETURN sys, env_prop, collect(event) as event")

        results = session.run("\n".join(query))

        # validate that property exists
        record = results.single()

        if not record:
            return None

        env_prop = dict(record.get("env_prop"))

        for event_prop in record.get("event"):
            env_prop[event_prop["event"]] = dict(event_prop)

        return env_prop

    @classmethod
    def _set_sys_env_props(
        cls, session, properties: dict, s_attr_prop: list, env_prop_type: SysEnvProperty
    ):
        """Update system environment properties"""

        s_attr_rand_prop = ["start", "end"]

        if "event" in properties and properties["event"]:
            event = properties["event"]
        else:
            event = None

        query = []

        query.append("MERGE (sys:SystemEnvironment { sref: 1 })")
        query.append(
            'MERGE (sys)-[:HAS_PROP]->(env_prop:EnvProp {{ name: "{}" }})'.format(
                env_prop_type.name
            )
        )

        if event:
            query.append(
                'MERGE (env_prop)-[:HAS_PROP]->(event:EnvProp {{ event: "{}" }})'.format(
                    event
                )
            )

        set_stm = []

        if event:
            set_stm.append(
                qh.get_set_stm(
                    properties, node_name="env_prop", supported_attr=s_attr_rand_prop
                )
            )
            set_stm.append(qh.get_set_stm(properties, "event", s_attr_prop))
        else:
            set_stm.append(
                qh.get_set_stm(
                    properties,
                    node_name="env_prop",
                    supported_attr=s_attr_rand_prop + s_attr_prop,
                )
            )

        query.extend(map(lambda x: "SET {}".format(x) if x else "", set_stm))

        return session.run("\n".join(query))

    @classmethod
    def set_voltage_props(cls, session, properties):
        """Set voltage properties
        Args:
            session: Graph Database session
        """
        s_attr_prop = ["mu", "sigma", "min", "max", "method", "rate", "enabled"]

        cls._set_sys_env_props(
            session, properties, s_attr_prop, env_prop_type=cls.SysEnvProperty.voltage
        )

    @classmethod
    def set_storage_randomizer_prop(cls, session, server_key, proptype, slc):
        """Update randranges for randomized argument
        Args:
            session: db session
            server_key: key of an asset that will have storage randoption configured
            proptype: name of a property
            slc: slice indicating start of random range and end of rando range
        """

        query = []

        strcli_query = (
            "MATCH (:ServerWithBMC {{ key: {} }})-[:SUPPORTS_STORCLI]->(strcli:Storcli)"
        )
        query.append(strcli_query.format(server_key))

        query.append(
            "SET strcli.{}='{}'".format(
                proptype, json.dumps({"start": slc.start, "end": slc.stop})
            )
        )

        session.run("\n".join(query))

    @classmethod
    def get_storage_randomizer_prop(cls, session, server_key, proptype):
        """Get randranges for configurable randomized arguments
        Args:
            session: graph db session
            server_key: key of a server holding randrange parameters
            proptype: storage property (e.g. physical drive error counts)
        """
        default_range = (0, 10)
        query = []

        strcli_query = (
            "MATCH (:ServerWithBMC {{ key: {} }})-[:SUPPORTS_STORCLI]->(strcli:Storcli)"
        )
        query.append(strcli_query.format(server_key))

        query.append("RETURN strcli.{} as randprop".format(proptype))
        record = session.run("\n".join(query)).single().get("randprop")

        if not record:
            return default_range

        rand_props = json.loads(record)
        return (rand_props["start"], rand_props["end"]) if rand_props else default_range

    @classmethod
    def get_thermal_cpu_details(cls, session, server_key):
        """Get ALL thermal relationships between a CPU and server sensors
        Args:
            session:  database session
            server_key(int): key of the server sensors belong to
        Returns:
            list: cpu/sensor relationships
        """

        results = session.run(
            """
            MATCH (:ServerWithBMC { key: $server })-[:HAS_SENSOR]->(sensor:Sensor)
            MATCH (:CPU)<-[rel:HEATED_BY]-(sensor)
            RETURN rel, sensor
            """,
            server=server_key,
        )

        th_cpu_details = []
        for record in results:
            sensor = dict(record.get("sensor"))
            th_cpu_details.append({"sensor": sensor, "rel": dict(record.get("rel"))})

        return th_cpu_details

    @classmethod
    def set_physical_drive_prop(cls, session, server_key, controller, did, properties):
        """Update physical drive properties (such as error counts or state)
        Args:
            session:  database session
            server_key(int): key of the server physical drive belongs to
            controller(int): controller number
            did(int): drive id 
            properties(dict): e.g. 'media_error_count', 'other_error_count'
                                   'predictive_error_count' or 'state'
        Returns:
            bool: True if properties were updated, 
                  False if controller and/or did are invalid 
        """
        query = []

        s_attr = [
            "media_error_count",
            "other_error_count",
            "predictive_error_count",
            "State",
            "time_stamp",
            "rebuild_time",
        ]

        properties["State"] = properties["state"] if "state" in properties else None

        # query as (server)->(storage_controller)->(physical drive)
        query.append("MATCH (server:Asset {{ key: {} }})".format(server_key))
        query.append(
            "MATCH (server)-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
                controller
            )
        )
        query.append(
            "MATCH (ctrl)-[:HAS_PHYSICAL_DRIVE]->(pd:PhysicalDrive {{ DID: {} }})".format(
                did
            )
        )

        # record uptime so that the rebuilding process gets simulated
        if properties["State"] and properties["State"] == "Onln":
            properties["time_stamp"] = time.time()

        set_stm = qh.get_set_stm(properties, node_name="pd", supported_attr=s_attr)
        query.append("SET {}".format(set_stm))
        query.append("RETURN ctrl, pd")

        result = session.run("\n".join(query)).single()

        return (result and result.get("ctrl") and result.get("pd")) is not None

    @classmethod
    def set_controller_prop(cls, session, server_key, controller, properties):
        """Update controller state
        Args:
            session:  database session
            server_key(int): key of the server controller belongs to
            controller(int): controller number
            properties(dict): settable controller props e.g. 'mem_c_errors', 'mem_uc_errors', 'alarm'
        Returns:
            bool: True if properties were updated, False if controller number is invalid
        """
        query = []

        s_attr = ["mem_c_errors", "mem_uc_errors", "alarm"]

        # query as (server)->(storage_controller)
        query.append("MATCH (server:Asset {{ key: {} }})".format(server_key))
        query.append(
            "MATCH (server)-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
                controller
            )
        )

        set_stm = qh.get_set_stm(properties, node_name="ctrl", supported_attr=s_attr)
        query.append("SET {}".format(set_stm))
        query.append("RETURN ctrl")

        result = session.run("\n".join(query)).single()

        return (result and result.get("ctrl")) is not None

    @classmethod
    def get_storcli_details(cls, session, server_key):
        """
        Args:
            session:  database session
            server_key(int): key of the server controller belongs to
        """

        results = session.run(
            """
            MATCH (:Asset { key: $key })-[:SUPPORTS_STORCLI]->(cli) RETURN cli
            """,
            key=server_key,
        )

        record = results.single()
        storcli_details = {}

        if record:
            storcli_details = dict(record.get("cli"))
            storcli_details["stateConfig"] = json.loads(storcli_details["stateConfig"])

        return storcli_details

    @classmethod
    def get_controller_details(cls, session, server_key, controller):
        """Query controller specs
        Args:
            session:  database session
            server_key(int): key of the server controller belongs to
            controller(int): controller number
        Returns:
            dict: controller information 
        """

        query = "MATCH (:Asset {{ key: {} }})-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }}) RETURN ctrl"
        results = session.run(query.format(server_key, controller))
        record = results.single()

        return dict(record.get("ctrl")) if record else None

    @classmethod
    def get_controller_count(cls, session, server_key):
        """Get number of controllers per server
        Args:
            session:  database session
            server_key(int): key of the server controller belongs to
        Returns:
            int: controller count
        """

        results = session.run(
            """
            MATCH (:Asset { key: $key })-[:HAS_CONTROLLER]->(ctrl:Controller) RETURN count(ctrl) as ctrl_count
            """,
            key=server_key,
        )

        record = results.single()
        return int(record.get("ctrl_count")) if record else None

    @classmethod
    def get_virtual_drive_details(cls, session, server_key, controller):
        """Get virtual drive details
        Args:
            session:  database session
            server_key(int): key of the server controller belongs to
            controller(int): controller number of VDs
        Returns:
            list: virtual drives
        """

        query = []
        query.append(
            "MATCH (:Asset {{ key: {} }})-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
                server_key, controller
            )
        )

        query.append("MATCH (ctrl)-[:HAS_VIRTUAL_DRIVE]->(vd:VirtualDrive)")
        query.append("MATCH (vd)<-[:BELONGS_TO_VIRTUAL_SPACE]-(pd:PhysicalDrive)")
        query.append("WITH vd, pd")
        query.append("ORDER BY pd.slotNum ASC")
        query.append("RETURN vd, collect(pd) as pd ORDER BY vd.vdNum ASC")

        results = session.run("\n".join(query))
        vd_details = [
            {**dict(r.get("vd")), **{"pd": list(map(dict, list(r.get("pd"))))}}
            for r in results
        ]

        return vd_details

    @classmethod
    def get_all_drives(cls, session, server_key, controller):
        """Get both virtual & physical drives for a particular server/raid controller
        Args:
            session:  database session
            server_key(int): key of the server controller belongs to
            controller(int): controller num
        Returns:
            dict: containing list of virtual & physical drives
        """

        query = []
        query.append(
            "MATCH (:Asset {{ key: {} }})-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
                server_key, controller
            )
        )
        query.append("MATCH (ctrl)-[:HAS_PHYSICAL_DRIVE]->(pd:PhysicalDrive)")

        query.append("RETURN collect(pd) as pd")

        results = session.run("\n".join(query))
        record = results.single()

        return {
            "vd": cls.get_virtual_drive_details(session, server_key, controller),
            "pd": list(map(dict, list(record.get("pd")))),
        }

    @classmethod
    def get_cachevault(
        cls, session, server_key, controller
    ):  # TODO: cachevault serial NUMBER!
        """Cachevault details
        Args:
            session:  database session
            server_key(int): key of the server cachevault belongs to
            controller(int): controller num
        Returns:
            dict: information about cachevault
        """
        query = []
        query.extend(
            [
                "MATCH (:Asset {{ key: {} }})-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
                    server_key, controller
                ),
                "MATCH (ctr)-[:HAS_CACHEVAULT]->(cv:CacheVault)",
                "RETURN cv",
            ]
        )

        results = session.run("\n".join(query))
        record = results.single()

        return dict(record.get("cv")) if record else None

    @classmethod
    def set_cv_replacement(
        cls, session, server_key, controller, repl_status, wt_on_fail
    ):  # TODO: cachevault serial NUMBER!
        """Update cachevault replacement status
        Args:
            session:  database session
            server_key(int): key of the server cachevault belongs to
            controller(int): controller num
        Returns:
            bool: True if properties were updated, False if controller number is invalid
        """

        query = []
        query.extend(
            [
                "MATCH (:Asset {{ key: {} }})-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
                    server_key, controller
                ),
                "MATCH (ctrl)-[:HAS_CACHEVAULT]->(cv:CacheVault)",
            ]
        )

        set_stm = qh.get_set_stm(
            {"replacement": repl_status, "writeThrough": wt_on_fail},
            node_name="cv",
            supported_attr=["replacement", "writeThrough"],
        )

        query.append("SET {}".format(set_stm))
        query.append("RETURN ctrl, cv")

        result = session.run("\n".join(query)).single()
        return (result and result.get("ctrl") and result.get("cv")) is not None

    @classmethod
    def add_to_hd_component_temperature(cls, session, target, temp_change, limit):
        """Add to cv temperature sensor value
        Args:
            session:  database session
            target(dict): target attributes such as key of the server, controller & serial number
            temp_change(int): value to be added to the target temperature
            limit(dict): indicates that target temp cannot go beyond this limit (upper & lower)
        Returns:
            tuple: True if the temp value was updated & current temp value (updated)
        """
        query = []
        query.extend(
            [
                "MATCH (:Asset {{ key: {} }})-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
                    target["server_key"], target["controller"]
                ),
                "MATCH (ctr)-[:HAS_CACHEVAULT|:HAS_PHYSICAL_DRIVE]->(hd_element:{} {{ {}: {} }})".format(
                    target["hd_type"], target["attribute"], target["value"]
                ),
                "RETURN hd_element.temperature as temp",
            ]
        )

        results = session.run("\n".join(query))
        record = results.single()
        current_temp = record.get("temp")

        new_temp = current_temp + temp_change

        new_temp = max(new_temp, limit["lower"])

        if "upper" in limit and limit["upper"]:
            new_temp = min(new_temp, limit["upper"])

        if new_temp == current_temp:
            return False, current_temp

        query = query[:2]  # grab first 2 queries
        query.append("SET hd_element.temperature={}".format(new_temp))

        session.run("\n".join(query))

        return True, new_temp

    @classmethod
    def get_all_hd_thermal_elements(cls, session, server_key):
        """Retrieve all storage components that support temperature sensors"""

        query = []
        query.extend(
            [
                "MATCH (:ServerWithBMC {{ key: {} }})-[:HAS_CONTROLLER]->(controller:Controller)".format(
                    server_key
                ),
                "MATCH (controller)-[:HAS_CACHEVAULT|:HAS_PHYSICAL_DRIVE]->(hd_component)",
                "WHERE hd_component:PhysicalDrive or hd_component:CacheVault",
                "RETURN controller, hd_component",
            ]
        )

        results = session.run("\n".join(query))

        hd_thermal_elements = []

        for record in results:
            hd_thermal_elements.append(
                {
                    "controller": dict(record.get("controller")),
                    "component": dict(record.get("hd_component")),
                }
            )

        return hd_thermal_elements

    @classmethod
    def get_psu_sensor_names(cls, session, server_key, psu_num):
        """Retrieve server-specific psu sensor names
        Args:
            session: database session
            server_key(int): key of the server sensors belongs to
            psu_num(int): psu num
        """

        query = []

        sensor_match = "MATCH (:PSU {{ key: {} }})<-[:HAS_COMPONENT]-(:Asset)-[:HAS_SENSOR]->(sensor {{ num: {} }})"
        label_match = map(
            "sensor:{}".format,
            ["psuCurrent", "psuTemperature", "psuStatus", "psuPower", "psuFan"],
        )

        query.extend(
            [
                sensor_match.format(server_key, psu_num),
                "WHERE {}".format(" or ".join(label_match)),
                "RETURN sensor",
            ]
        )

        results = session.run("\n".join(query))

        psu_names = {}
        for record in results:
            entry = dict(record.get("sensor"))
            psu_names[entry["type"]] = entry["name"]

        return psu_names

    @classmethod
    def set_play_path(cls, session, path):
        """Update path to the folder containing playbooks
        Args:
            session: database session
            path(str): absolute path to the script folder
        """

        session.run("MERGE (n:Playback { sref: 1 }) SET n.path=$path", path=path)

    @classmethod
    def get_play_path(cls, session):
        """Get play folder
        Args:
            session: database session
        Returns:
            str: path to the plays/scripts
        """

        results = session.run("MATCH (n:Playback { sref: 1 }) RETURN n.path as path")
        record = results.single()
        play_folder = ""

        if record:
            play_folder = record.get("path")

        return play_folder
