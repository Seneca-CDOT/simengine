"""Add asset to a system model or update/create connection(s). 
This module provides high-level control over system model. 
"""
import json
import os
from enum import Enum
import time
import sys
import libvirt

from enginecore.model.graph_reference import GraphReference
from enginecore.model.supported_sensors import SUPPORTED_SENSORS

import enginecore.tools.query_helpers as qh

GRAPH_REF = GraphReference()

# attributes shared by all the assets
CREATE_SHARED_ATTR = [
    "x",
    "y",
    "name",
    "type",
    "key",
    "off_delay",
    "on_delay",
    "min_voltage",
    "power_on_ac",
]
# Labels used by the app
SIMENGINE_NODE_LABELS = []
SIMENGINE_NODE_LABELS.extend(["Asset", "StageLayout", "SystemEnvironment", "EnvProp"])
SIMENGINE_NODE_LABELS.extend(["OID", "OIDDesc", "Sensor", "AddressSpace"])
SIMENGINE_NODE_LABELS.extend(["CPU", "Battery"])
SIMENGINE_NODE_LABELS.extend(
    ["Controller", "Storcli", "BBU", "CacheVault", "VirtualDrive", "PhysicalDrive"]
)
SIMENGINE_NODE_LABELS.extend(["Playback"])


def _add_psu(key, psu_index, attr):
    """Add a PSU to an existing server
    
    Args:
        key(int): server key psu will belong to
        psu_index(int): psu number
        attr(dict): psu attributes such as power_source, power_consumption, variation & draw
    """

    with GRAPH_REF.get_session() as session:

        query = []
        # find the server
        query.append("MATCH (asset:Asset {{ key: {} }})".format(key))

        # create a PSU
        attr["key"] = int("{}{}".format(key, psu_index))
        attr["name"] = "psu" + str(psu_index)
        attr["type"] = "psu"

        props_stm = qh.get_props_stm(attr)
        query.append("CREATE (psu:Asset:PSU:Component {{ {} }})".format(props_stm))

        # set relationships
        query.append("CREATE (asset)-[:HAS_COMPONENT]->(psu)")
        query.append("CREATE (asset)-[:POWERED_BY]->(psu)")

        session.run("\n".join(query))


def configure_asset(key, attr):
    """Update existing properties
    
    Args:
        key(int): key of the asset to be configured
        attr(dict): asset props' updates
    """

    if "asset_key" in attr and attr["asset_key"]:
        del attr["asset_key"]

    with GRAPH_REF.get_session() as session:

        set_statement = qh.get_set_stm(attr)
        query = "MATCH (asset:Asset {{ key: {key} }}) SET {set_stm}".format(
            key=key, set_stm=set_statement
        )

        session.run(query)


def remove_link(source_key, dest_key):
    """Remove existing power connection
    
    Args:
        source_key(int): key of the parent asset
        dest_key(int): key of the asset powered by source_key
    """

    with GRAPH_REF.get_session() as session:
        session.run(
            """
        MATCH (src:Asset {key: $src_key})<-[power_link:POWERED_BY]-(dst:Asset {key: $dest_key})
        DELETE power_link
        """,
            src_key=source_key,
            dest_key=dest_key,
        )


def link_assets(source_key, dest_key):
    """Power a component by another component 

    Args:
        source_key(int): key of the parent asset
        dest_key(int): key of the asset to be powered by the parent
    """

    with GRAPH_REF.get_session() as session:

        # Validate that the asset does not power already existing device
        result = session.run(
            """
            MATCH (src:Asset {key: $source_key})<-[:POWERED_BY]-(existing_dest:Asset) RETURN existing_dest
        """,
            source_key=source_key,
        )

        record = result.single()
        if record:
            print("The source asset already powers an existing asset!", file=sys.stderr)
            return

        result = session.run(
            """
            MATCH (src:Asset {key: $dest_key})-[:POWERED_BY]->(existing_src:Asset) RETURN existing_src
        """,
            dest_key=dest_key,
        )

        record = result.single()
        if record:
            print(
                "The destination asset is already powered by an existing asset!",
                file=sys.stderr,
            )
            return

        result = session.run(
            "MATCH (dst:Asset {key: $dest_key})-[:HAS_COMPONENT]->(src:Asset {key: $source_key}) RETURN src",
            source_key=source_key,
            dest_key=dest_key,
        )
        record = result.single()
        if record:
            print("Asset cannot power itself!", file=sys.stderr)
            return

        # Create a link
        result = session.run(
            """
        MATCH (src:Asset {key: $source_key})
        WHERE NOT src:PDU and NOT src:UPS and NOT src:Server and NOT src:ServerWithBMC
        MATCH (dst:Asset {key: $dest_key})
        WHERE NOT dst:Server and NOT dst:ServerWithBMC and (NOT dst:Component or dst:PSU) 
        CREATE (dst)-[r:POWERED_BY]->(src) return r as link
        """,
            source_key=source_key,
            dest_key=dest_key,
        )

        record = result.single()

        if (not record) or ("link" not in dict(record)):
            print("Invalid link configuration was provided")


def create_outlet(key, attr):
    """Add outlet to the model 
    
     Args:
        key(int): unique key to be assigned
        attr(dict): asset properties
    """

    with GRAPH_REF.get_session() as session:
        attr["name"] = (
            attr["name"] if "name" in attr and attr["name"] else "out-{}".format(key)
        )

        s_attr = CREATE_SHARED_ATTR
        props_stm = qh.get_props_stm(
            {**attr, **{"type": "outlet", "key": key}}, supported_attr=s_attr
        )
        session.run("CREATE (:Asset:Outlet {{ {} }})".format(props_stm))


class ServerVariations(Enum):
    """Supported variations of the server asset """

    Server = 1
    ServerWithBMC = 2


IPMI_LAN_DEFAULTS = {
    "user": "ipmiusr",
    "password": "test",
    "host": "localhost",
    "interface": "",
    "port": 9001,
    "vmport": 9002,
    "storcli_port": 50000,
    "storcli_enabled": True,
}


def _add_sensors(asset_key, preset_file):
    """Add sensors based on a preset file"""

    with open(preset_file) as preset_handler, GRAPH_REF.get_session() as session:
        query = []

        query.append("MATCH (server:Asset {{ key: {} }})".format(asset_key))
        data = json.load(preset_handler)

        for sensor_type, sensor_specs in data.items():

            if sensor_type not in SUPPORTED_SENSORS:
                continue

            address_space_exists = (
                "addressSpace" in sensor_specs and sensor_specs["addressSpace"]
            )

            if address_space_exists:
                address_space = repr(sensor_specs["addressSpace"])
                query.append(
                    "CREATE (aSpace{}:AddressSpace {{ address: {} }})".format(
                        sensor_specs["addressSpace"], address_space
                    )
                )

            for idx, sensor in enumerate(sensor_specs["sensorDefinitions"]):

                sensor_node = "{}{}".format(sensor_type, idx)

                if "address" in sensor and sensor["address"]:
                    addr = {"address": hex(int(sensor["address"], 16))}
                elif address_space_exists:
                    addr = {"index": idx}
                else:
                    raise KeyError(
                        "Missing address for a sensor {}".format(sensor_type)
                    )

                s_attr = [
                    "name",
                    "defaultValue",
                    "offValue",
                    "group",
                    "num",
                    "lnr",
                    "lcr",
                    "lnc",
                    "unc",
                    "ucr",
                    "unr",
                    "address",
                    "index",
                    "type",
                    "eventReadingType",
                ]

                sensor["name"] = sensor["name"].format(
                    index=addr["index"] + 1 if "index" in addr else ""
                )
                props = {
                    **sensor["thresholds"],
                    **sensor,
                    **addr,
                    **sensor_specs,
                    **{"type": sensor_type, "num": idx + 1},
                }

                props_stm = qh.get_props_stm(props, supported_attr=s_attr)
                query.append(
                    "CREATE (sensor{}:Sensor:{} {{ {} }})".format(
                        sensor_node, sensor_type, props_stm
                    )
                )

                if not ("address" in sensor) or not sensor["address"]:
                    query.append(
                        "CREATE (sensor{})-[:HAS_ADDRESS_SPACE]->(aSpace{})".format(
                            sensor_node, sensor_specs["addressSpace"]
                        )
                    )

                query.append(
                    "CREATE (server)-[:HAS_SENSOR]->(sensor{})".format(sensor_node)
                )

        # print("\n".join(query))
        session.run("\n".join(query))


def _add_storage(asset_key, preset_file, storage_state_file):
    """Add storage to the server with asset_key"""

    with open(preset_file) as preset_h, open(
        storage_state_file
    ) as state_h, GRAPH_REF.get_session() as session:
        query = []

        query.append("MATCH (server:Asset {{ key: {} }})".format(asset_key))
        storage_data = json.load(preset_h)
        state_data = json.load(state_h)

        props_stm = qh.get_props_stm(
            {**storage_data, **{"stateConfig": json.dumps(state_data)}},
            supported_attr=["operatingSystem", "CLIVersion", "stateConfig"],
        )
        query.append(
            "CREATE (server)-[:SUPPORTS_STORCLI]->(storage:Storcli {{ {} }})".format(
                props_stm
            )
        )

        for idx, controller in enumerate(storage_data["controllers"]):

            s_attr = [
                "controllerNum",
                "model",
                "serialNumber",
                "SASAddress",
                "PCIAddress",
                "mfgDate",
                "reworkDate",
                "memoryCorrectable_errors",
                "memoryUncorrectable_errors",
                "alarmState",
                "numDriveGroups",
                "bgiRate",
                "prRate",
                "rebuildRate",
                "ccRate",
            ]

            default_ctr_prop = {
                "memoryCorrectable_errors": 0,
                "memoryUncorrectable_errors": 0,
                "alarmState": "off",
                "controllerNum": idx,
            }
            props_stm = qh.get_props_stm(
                {**controller, **default_ctr_prop}, supported_attr=s_attr
            )

            ctrl_node = "ctrl" + str(idx)
            query.append(
                "CREATE (server)-[:HAS_CONTROLLER]->({}:Controller {{ {} }})".format(
                    ctrl_node, props_stm
                )
            )

            # BBU or CacheVault
            if "BBU" in controller and controller["BBU"]:
                props_stm = qh.get_props_stm(
                    controller["BBU"],
                    supported_attr=[
                        "model",
                        "serialNumber",
                        "type",
                        "replacementNeeded",
                        "state",
                        "designCapacity",
                    ],
                )
                query.append(
                    "CREATE ({})-[:HAS_BBU]->(bbu:BBU {{ {} }})".format(
                        ctrl_node, props_stm
                    )
                )
            elif "CacheVault" in controller and controller["CacheVault"]:
                props_stm = qh.get_props_stm(
                    {
                        **controller["CacheVault"],
                        **{"temperature": 0, "replacement": "No", "writeThrough": True},
                    },
                    supported_attr=[
                        "model",
                        "replacement",
                        "state",
                        "temperature",
                        "mfgDate",
                        "serialNumber",
                        "writeThrough",
                    ],
                )
                query.append(
                    "CREATE ({})-[:HAS_CACHEVAULT]->(cache:CacheVault {{ {} }})".format(
                        ctrl_node, props_stm
                    )
                )

            # Add physical drives
            for pidx, phys_drive in enumerate(controller["PD"]):

                pd_node = "pd" + str(phys_drive["DID"])

                # define supported attributes
                s_attr = [
                    "EID",
                    "DID",
                    "State",
                    "DG",
                    "Size",
                    "Intf",
                    "Med",
                    "SED",
                    "PI",
                    "SeSz",
                    "Model",
                    "Sp",
                    "Type",
                    "PDC",
                    "slotNum",
                    "temperature",
                    "mediaErrorCount",
                    "otherErrorCount",
                    "predictiveErrorCount",
                    "rebuildTime",
                    "timeStamp",
                    "manufacturerId",
                    "serialNumber",
                ]

                props_stm = qh.get_props_stm(
                    {
                        **phys_drive,
                        **{
                            "slotNum": pidx,
                            "mediaErrorCount": 0,
                            "otherErrorCount": 0,
                            "predictiveErrorCount": 0,
                            "temperature": 0,
                            "timeStamp": time.time(),
                        },
                    },
                    supported_attr=s_attr,
                )

                query.append(
                    "CREATE ({})-[:HAS_PHYSICAL_DRIVE]->({}:PhysicalDrive {{ {} }})".format(
                        ctrl_node, pd_node, props_stm
                    )
                )

            for vidx, virt_drive in enumerate(controller["VD"]):
                vd_node = "vd" + str(vidx)

                s_attr = [
                    "TYPE",
                    "DG",
                    "State",
                    "Access",
                    "Cac",
                    "Cache",
                    "Name",
                    "Consist",
                    "sCC",
                    "Size",
                    "vdNum",
                ]

                props_stm = qh.get_props_stm(
                    {**virt_drive, **{"vdNum": vidx}}, supported_attr=s_attr
                )

                query.append(
                    "CREATE ({})-[:HAS_VIRTUAL_DRIVE]->({}:VirtualDrive {{ {} }})".format(
                        ctrl_node, vd_node, props_stm
                    )
                )

                # connect PDs & VDs
                for pidx in virt_drive["DID"]:

                    query.append(
                        "CREATE ({})<-[:BELONGS_TO_VIRTUAL_SPACE]-(pd{})".format(
                            vd_node, pidx
                        )
                    )

        # print("\n".join(query))
        session.run("\n".join(query))


def create_server(key, attr, server_variation=ServerVariations.Server):
    """Create a simulated server """

    if not attr["power_consumption"]:
        raise KeyError("Server asset requires power_consumption attribute")
    if not attr["domain_name"]:
        raise KeyError("Must provide VM name (domain name)")

    # Validate server domain name
    try:
        conn = libvirt.open("qemu:///system")
        conn.lookupByName(attr["domain_name"])
    except libvirt.libvirtError:
        raise KeyError("VM does not exist")
    finally:
        conn.close()

    with GRAPH_REF.get_session() as session:

        query = []  # cypher query

        attr["name"] = (
            attr["name"] if "name" in attr and attr["name"] else attr["domain_name"]
        )
        attr["type"] = server_variation.name.lower()
        attr["key"] = key

        s_attr = [
            "domain_name",
            "power_consumption",
            "power_source",
        ] + CREATE_SHARED_ATTR
        props_stm = qh.get_props_stm(attr, supported_attr=s_attr)

        # create a server
        query.append(
            "CREATE (server:Asset  {{ {} }}) SET server :{}".format(
                props_stm, server_variation.name
            )
        )
        query.append("CREATE (server)-[:HAS_CPU]->(:CPU)")

        # set BMC-server specific attributes if type is bmc
        if server_variation == ServerVariations.ServerWithBMC:

            bmc_attr = {**IPMI_LAN_DEFAULTS, **attr}  # merge

            set_stm = qh.get_set_stm(
                bmc_attr, node_name="server", supported_attr=IPMI_LAN_DEFAULTS.keys()
            )
            query.append("SET {}".format(set_stm))

        session.run("\n".join(query))

        if server_variation == ServerVariations.ServerWithBMC:

            # if preset is provided -> use the user-defined file
            f_loc = os.path.dirname(__file__)
            s_def_file = (
                lambda p, j: os.path.expanduser(attr[p])
                if p in attr and attr[p]
                else os.path.join(f_loc, "presets/" + j)
            )

            sensor_file = s_def_file("sensor_def", "sensors.json")
            storage_def_file = s_def_file("storage_def", "storage.json")
            storage_state_file = s_def_file("storage_states", "storage_states.json")

            _add_sensors(key, sensor_file)
            _add_storage(key, storage_def_file, storage_state_file)

        if server_variation == ServerVariations.ServerWithBMC:
            with open(
                sensor_file
            ) as preset_handler, GRAPH_REF.get_session() as session:
                data = json.load(preset_handler)
                for psu in data["psu"]:
                    _add_psu(key, psu_index=psu["id"], attr=psu)

        else:
            # add PSUs to the model
            for i in range(attr["psu_num"]):
                psu_attr = {
                    "power_consumption": attr["psu_power_consumption"],
                    "power_source": attr["psu_power_source"],
                    "variation": server_variation.name.lower(),
                    "draw": attr["psu_load"][i] if attr["psu_load"] else 1,
                    "id": i,
                }
                _add_psu(key, psu_index=i + 1, attr=psu_attr)


def create_ups(
    key,
    attr,
    preset_file=os.path.join(os.path.dirname(__file__), "presets/apc_ups.json"),
):
    """Add UPS to the system model """

    preset_file = (
        attr["snmp_preset"]
        if "snmp_preset" in attr and attr["snmp_preset"]
        else preset_file
    )

    with open(preset_file) as preset_handler, GRAPH_REF.get_session() as session:

        query = []
        data = json.load(preset_handler)

        attr["name"] = (
            attr["name"] if "name" in attr and attr["name"] else data["assetName"]
        )
        attr["runtime"] = json.dumps(data["modelRuntime"], sort_keys=True)

        s_attr = [
            "staticOidFile",
            "port",
            "host",
            "outputPowerCapacity",
            "minPowerOnBatteryLevel",
            "fullRechargeTime",
            "runtime",
            "power_source",
            "power_consumption",
            "work_dir",
            "interface",
            "mask",
        ] + CREATE_SHARED_ATTR

        props_stm = qh.get_props_stm(
            {**attr, **data, **{"key": key, "type": "ups"}}, supported_attr=s_attr
        )

        # create UPS asset
        query.append("CREATE (ups:Asset:UPS:SNMPSim {{ {} }})".format(props_stm))

        # add batteries (only one for now)
        query.append(
            "CREATE (bat:UPSBattery:Battery { name: 'bat1', type: 'battery' })"
        )
        query.append("CREATE (ups)-[:HAS_BATTERY]->(bat)")
        query.append("CREATE (ups)-[:POWERED_BY]->(bat)")

        # Add UPS OIDs
        for oid_key, oid_props in data["OIDs"].items():
            if oid_key == "SerialNumber":
                if "serial_number" in attr and attr["serial_number"]:
                    oid_props["defaultValue"] = attr["serial_number"]
                else:
                    oid_props["defaultValue"] = qh.generate_id()

            if oid_key == "MAC":
                if "mac_address" in attr and attr["mac_address"]:
                    oid_props["defaultValue"] = attr["mac_address"]
                else:
                    oid_props["defaultValue"] = qh.generate_mac()

            props = {**oid_props, **{"OIDName": oid_key}}
            props_stm = qh.get_props_stm(
                props, ["OID", "dataType", "defaultValue", "OIDName"]
            )

            query.append("CREATE ({}:OID {{ {} }})".format(oid_key, props_stm))
            query.append("CREATE (ups)-[:HAS_OID]->({})".format(oid_key))

            if "oidDesc" in oid_props and oid_props["oidDesc"]:
                oid_desc = dict((y, x) for x, y in oid_props["oidDesc"].items())
                desc_stm = qh.get_oid_desc_stm(oid_desc)
                query.append(
                    "CREATE ({}Desc:OIDDesc {{ {} }})".format(oid_key, desc_stm)
                )
                query.append(
                    "CREATE ({})-[:HAS_STATE_DETAILS]->({}Desc)".format(
                        oid_key, oid_key
                    )
                )

            if oid_key == "PowerOff":
                query.append("CREATE (ups)-[:POWERED_BY]->({})".format(oid_key))

        # Set output outlets
        for i in range(data["numOutlets"]):

            props = {
                "name": "out" + str(i + 1),
                "type": "outlet",
                "key": int("{}{}".format(key, str(i + 1))),
            }
            props_stm = qh.get_props_stm(props)
            query.append(
                "CREATE (out{}:Asset:Outlet:Component {{ {} }})".format(i, props_stm)
            )
            query.append("CREATE (ups)-[:HAS_COMPONENT]->(out{})".format(i))
            query.append("CREATE (out{})-[:POWERED_BY]->(ups)".format(i))

        session.run("\n".join(query))


def create_pdu(
    key,
    attr,
    preset_file=os.path.join(os.path.dirname(__file__), "presets/apc_pdu.json"),
):
    """Add PDU to the model """

    preset_file = (
        attr["snmp_preset"]
        if "snmp_preset" in attr and attr["snmp_preset"]
        else preset_file
    )
    with open(preset_file) as preset_handler, GRAPH_REF.get_session() as session:

        query = []
        data = json.load(preset_handler)
        outlet_count = data["OIDs"]["OutletCount"]["defaultValue"]

        attr["name"] = (
            attr["name"] if "name" in attr and attr["name"] else data["assetName"]
        )
        s_attr = [
            "staticOidFile",
            "port",
            "host",
            "interface",
            "mask",
        ] + CREATE_SHARED_ATTR

        props_stm = qh.get_props_stm(
            {**attr, **data, **{"key": key, "type": "pdu"}}, supported_attr=s_attr
        )

        # create PDU asset
        query.append("CREATE (pdu:Asset:PDU:SNMPSim {{ {} }})".format(props_stm))

        # Add PDU OIDS to the model
        for oid_key, oid_props in data["OIDs"].items():
            if "serial_number" in attr and attr["serial_number"]:
                oid_props["defaultValue"] = attr["serial_number"]
            else:
                oid_props["defaultValue"] = qh.generate_id()

            if oid_key == "MAC":
                if "mac_address" in attr and attr["mac_address"]:
                    oid_props["defaultValue"] = attr["mac_address"]
                else:
                    oid_props["defaultValue"] = qh.generate_mac()

            s_attr = ["OID", "OIDName", "defaultValue", "dataType"]
            props_stm = qh.get_props_stm(
                {**oid_props, **{"OIDName": oid_key}}, supported_attr=s_attr
            )
            query.append(
                "CREATE (:OID {{ {props_stm} }})<-[:HAS_OID]-(pdu)".format(
                    props_stm=props_stm
                )
            )

        # Outlet-specific OIDs
        for oid_key, oid_props in data["outletOIDs"].items():

            # For outlet state, Outlet asset will need to be created
            if oid_key == "OutletState":

                oid_desc = dict((y, x) for x, y in oid_props["oidDesc"].items())

                desc_stm = qh.get_oid_desc_stm(oid_desc)
                query.append("CREATE (oidDesc:OIDDesc {{ {} }})".format(desc_stm))

                for j in range(outlet_count):

                    out_key = int("{}{}".format(key, str(j + 1)))
                    props_stm = qh.get_props_stm(
                        {"key": out_key, "name": "out" + str(j + 1), "type": "outlet"}
                    )

                    # create outlet per OID
                    query.append(
                        "CREATE (out{}:Asset:Outlet:Component {{ {} }})".format(
                            out_key, props_stm
                        )
                    )

                    # set outlet relationships
                    query.append("CREATE (out{})-[:POWERED_BY]->(pdu)".format(out_key))
                    query.append(
                        "CREATE (pdu)-[:HAS_COMPONENT]->(out{})".format(out_key)
                    )

                    # create OID associated with outlet & pdu
                    for oid_n, oid in enumerate(oid_props["OID"]):

                        out_key = int("{}{}".format(key, str(j + 1)))
                        oid = oid + "." + str(j + 1)
                        oid_node_name = "{oid_name}{outlet_num}{oid_num}".format(
                            oid_name=oid_key, outlet_num=j, oid_num=oid_n
                        )

                        props_stm = qh.get_props_stm(
                            {
                                "OID": oid,
                                "OIDName": oid_key,
                                "dataType": oid_props["dataType"],
                                "defaultValue": oid_props["defaultValue"],
                            }
                        )

                        query.append(
                            "CREATE ({oid_node_name}:OID {{ {props_stm} }})".format(
                                oid_node_name=oid_node_name, props_stm=props_stm
                            )
                        )

                        # set the relationships (outlet powerd by state oid etc..)
                        query.append(
                            "CREATE (out{})-[:POWERED_BY]->({})".format(
                                out_key, oid_node_name
                            )
                        )
                        query.append(
                            "CREATE ({})-[:HAS_STATE_DETAILS]->(oidDesc)".format(
                                oid_node_name
                            )
                        )
                        query.append(
                            "CREATE (pdu)-[:HAS_OID]->({})".format(oid_node_name)
                        )
            else:
                oid = oid_props["OID"]

                props_stm = qh.get_props_stm(
                    {
                        "OID": oid,
                        "OIDName": oid_key,
                        "dataType": oid_props["dataType"],
                        "defaultValue": oid_props["defaultValue"],
                    }
                )

                query.append("CREATE ({}:OID {{ {} }})".format(oid_key, props_stm))
                query.append("CREATE (pdu)-[:HAS_OID]->({})".format(oid_key))

        # print("\n".join(query))
        session.run("\n".join(query))


def create_static(key, attr, static_type="StaticAsset"):
    """Create Dummy static asset"""
    if not attr["power_consumption"]:
        raise KeyError("Static asset requires power_consumption")

    with GRAPH_REF.get_session() as session:
        s_attr = ["img_url", "power_consumption", "power_source"] + CREATE_SHARED_ATTR
        props_stm = qh.get_props_stm(
            {**attr, **{"type": static_type.lower(), "key": key}}, supported_attr=s_attr
        )
        session.run("CREATE (:Asset:{} {{ {} }})".format(static_type, props_stm))


def create_lamp(key, attr):
    """Create Dummy lamp asset"""
    create_static(key, attr, static_type="Lamp")


def drop_model():
    """ Drop system model """
    with GRAPH_REF.get_session() as session:
        session.run(
            "MATCH (a) WHERE {} DETACH DELETE a".format(
                " OR ".join(map("a:{}".format, SIMENGINE_NODE_LABELS))
            )
        )


def delete_asset(key):
    """ Delete by key """
    with GRAPH_REF.get_session() as session:
        session.run(
            """MATCH (a:Asset { key: $key })
        OPTIONAL MATCH (a)-[:HAS_COMPONENT]->(s)
        OPTIONAL MATCH (a)-[:HAS_OID]->(oid)
        OPTIONAL MATCH (a)-[:HAS_BATTERY]->(b)
        OPTIONAL MATCH (oid)-[:HAS_STATE_DETAILS]->(sd)
        OPTIONAL MATCH (a)-[:HAS_CPU]->(cp)
        OPTIONAL MATCH (a)-[:HAS_SENSOR]->(sn)
        OPTIONAL MATCH (sn)-[:HAS_ADDRESS_SPACE]->(as)
        DETACH DELETE a,s,oid,sd,b,sn,as,cp""",
            key=key,
        )


def set_thermal_storage_target(attr):
    """Set up storage components as thermal targets for IPMI sensor
    Returns:
        bool: True if a new relationship was created
    """

    query = []

    # find the source sensor & server asset
    query.append(
        'MATCH (source {{ name: "{}" }} )<-[:HAS_SENSOR]-(server:Asset {{ key: {} }})'.format(
            attr["source_sensor"], attr["asset_key"]
        )
    )

    query.append(
        "MATCH (server)-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
            attr["controller"]
        )
    )

    if attr["cache_vault"]:
        query.append(
            'MATCH (ctrl)-[:HAS_CACHEVAULT]->(target:CacheVault {{ serialNumber: "{}" }})'.format(
                attr["cache_vault"]
            )
        )
    elif attr["drive"]:
        query.append(
            "MATCH (ctrl)-[:HAS_PHYSICAL_DRIVE]->(target:PhysicalDrive {{ DID: {} }})".format(
                attr["drive"]
            )
        )
    else:
        raise KeyError("Must provide either target drive or cache_vault")

    return _set_thermal_target(attr, query)


def _set_thermal_target(attr, query):
    """Set thermal relationship between 2 ndoes
    Args:
        attr(dict): relationship properties (such as rate, event, degrees etc. )
        query(list): query that includes look up of the 'target' & 'source' nodes
    Returns:
        bool: True if the relationship is new
    """

    # determine relationship type
    thermal_rel_type = ""
    if attr["action"] == "increase":
        thermal_rel_type = "HEATED_BY"
    elif attr["action"] == "decrease":
        thermal_rel_type = "COOLED_BY"
    else:
        raise KeyError("Unrecognized event type: {}".format(attr["event"]))

    # fist check if the relationship already exists
    rel_query = []
    rel_query.append("MATCH (source)<-[ex_rel:{}]-(target)".format(thermal_rel_type))
    rel_query.append("RETURN ex_rel")

    with GRAPH_REF.get_session() as session:

        result = session.run("\n".join(query + rel_query))
        rel_exists = result.single()

        # set the thermal relationship & relationship attributes
        s_attr = ["pause_at", "rate", "event", "degrees", "jitter", "action", "model"]
        set_stm = qh.get_set_stm(attr, node_name="rel", supported_attr=s_attr)

        query.append("MERGE (source)<-[rel:{}]-(target)".format(thermal_rel_type))
        query.append("SET {}".format(set_stm))

        session.run("\n".join(query))
        return rel_exists is None


def set_thermal_sensor_target(attr):
    """Set-up a new thermal relationship between 2 sensors or configure the existing one
    Returns:
        bool: True if a new relationship was created
    """

    if attr["source_sensor"] == attr["target_sensor"]:
        raise KeyError("Sensor cannot affect itself!")

    query = []

    # find the source sensor & server asset
    query.append(
        'MATCH (source {{ name: "{}" }} )<-[:HAS_SENSOR]-(server:Asset {{ key: {} }})'.format(
            attr["source_sensor"], attr["asset_key"]
        )
    )

    # find the destination or target sensor
    query.append(
        'MATCH (target {{ name: "{}" }} )<-[:HAS_SENSOR]-(server)'.format(
            attr["target_sensor"]
        )
    )

    return _set_thermal_target(attr, query)


def set_thermal_cpu_target(attr):
    """Set-up a new thermal relationship between a sensor and CPU load 
    of the server sensor belongs to

    Returns:
        bool: True if a new relationship was created
    """

    try:
        _ = json.loads(attr["model"])
    except ValueError as error:
        raise ValueError("Model .json is not valid: {}".format(error))

    query = []

    # find the source sensor & server asset
    query.append(
        "MATCH (cpu:CPU)<-[:HAS_CPU]-(server:Asset {{ key: {} }})".format(
            attr["asset_key"]
        )
    )

    # find the destination or target sensor
    query.append(
        'MATCH (target {{ name: "{}" }} )<-[:HAS_SENSOR]-(server)'.format(
            attr["target_sensor"]
        )
    )

    # set the thermal relationship & relationship attributes
    set_stm = qh.get_set_stm(attr, node_name="rel", supported_attr=["model"])

    query.append("MERGE (cpu)<-[rel:HEATED_BY]-(target)")
    query.append("SET {}".format(set_stm))

    rel_query = []
    rel_query.append("MATCH (cpu)<-[ex_rel:HEATED_BY]-(target)")
    rel_query.append("RETURN ex_rel")

    with GRAPH_REF.get_session() as session:
        result = session.run("\n".join(query[0:2] + rel_query))
        rel_exists = result.single()

        session.run("\n".join(query))
        return rel_exists is None


def delete_thermal_sensor_target(attr):
    """Remove thermal relationship between 2 sensors"""

    query = []

    # find the source sensor & server asset
    query.append(
        'MATCH (source {{ name: "{}" }} )<-[:HAS_SENSOR]-(:Asset {{ key: {} }})'.format(
            attr["source_sensor"], attr["asset_key"]
        )
    )

    # find the destination or target sensor & save its thermal link
    query.append(
        'MATCH (source)<-[thermal_link {{ event: "{}" }}]-(:Sensor {{ name: "{}" }})'.format(
            attr["event"], attr["target_sensor"]
        )
    )

    query.append("DELETE thermal_link")  # delete the connection

    with GRAPH_REF.get_session() as session:
        session.run("\n".join(query))


def delete_thermal_cpu_target(attr):
    """Remove thermal relationship between CPU and """

    query = []

    # find the source sensor & server asset
    query.append(
        'MATCH (target {{ name: "{}" }} )<-[:HAS_SENSOR]-(:Asset {{ key: {} }})'.format(
            attr["target_sensor"], attr["asset_key"]
        )
    )

    query.append("MATCH (target)-[thermal_link:HEATED_BY]->(:CPU)")
    query.append("DELETE thermal_link")  # delete the connection

    with GRAPH_REF.get_session() as session:
        session.run("\n".join(query))


def delete_thermal_storage_target(attr):
    """Remove a connection between a sensor and storage component"""
    query = []

    # find the source sensor & server asset
    query.append(
        'MATCH (source {{ name: "{}" }} )<-[:HAS_SENSOR]-(server:Asset {{ key: {} }})'.format(
            attr["source_sensor"], attr["asset_key"]
        )
    )

    # find the destination or target
    if "cache_vault" in attr and attr["cache_vault"]:
        target_prop = ':CacheVault {{ serialNumber: "{}" }}'.format(attr["cache_vault"])
    elif "drive" in attr and attr["drive"]:
        target_prop = ":PhysicalDrive {{ DID: {} }}".format(attr["drive"])

    query.append(
        "MATCH (server)-[:HAS_CONTROLLER]->(ctrl:Controller {{ controllerNum: {} }})".format(
            attr["controller"]
        )
    )

    ctrl_str_element_rel = ":HAS_CACHEVAULT|:HAS_PHYSICAL_DRIVE"

    # find either a physical drive or cachevault affected by the source sensor
    # that belongs to certain controller
    query.append(
        'MATCH (source)<-[thermal_link {{ event: "{}" }}]-({})<-[{}]-(ctrl)'.format(
            attr["event"], target_prop, ctrl_str_element_rel
        )
    )

    query.append("DELETE thermal_link")  # delete the connection

    with GRAPH_REF.get_session() as session:
        session.run("\n".join(query))
