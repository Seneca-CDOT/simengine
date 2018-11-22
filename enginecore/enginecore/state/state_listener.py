"""StateListener monitors any updates to assets/OIDs 
& determines if the event affects other (connected) assets

The daemon initializes a WebSocket & Redis event listener component
and reacts to state updates by dispatching cuircuit events that are, in turn,
handled by individual assets.

"""
import json
import logging

from circuits import Component, Event, Timer, Worker, Debugger, task
import redis

from circuits.web import Logger, Server, Static
from circuits.web.dispatchers import WebSocketsDispatcher

from enginecore.state.assets import Asset, SystemEnvironment, PowerEventResult, LoadEventResult
from enginecore.state.state_managers import StateManager
from enginecore.state.event_map import PowerEventManager
from enginecore.state.web_socket import WebSocket, ClientRequests
from enginecore.state.redis_channels import RedisChannels
from enginecore.model.graph_reference import GraphReference
from enginecore.state.state_initializer import initialize, clear_temp

SOCKET_CONF = {'host': "0.0.0.0", 'port': 8000}

class NotifyClient(Event):
    """Notify websocket clients of any data updates"""

class StateListener(Component):
    """Top-level component that instantiates assets & maps redis events to circuit events"""


    def __init__(self, debug=False, force_snmp_init=False):
        super(StateListener, self).__init__()

        ### Set-up WebSocket & Redis listener ###
        logging.info('Starting simengine daemon...')

        # Use redis pub/sub communication
        logging.info('Initializing redis connection...')
        self._redis_store = redis.StrictRedis(host='localhost', port=6379)

        self._bat_pubsub = self._redis_store.pubsub()
        self._state_pubsub = self._redis_store.pubsub()
        self._thermal_pubsub = self._redis_store.pubsub()

        # assets will store all the devices/items including PDUs, switches etc.
        self._assets = {}
        self._sys_environ = SystemEnvironment().register(self)

        # set default state
        StateManager.power_restore()

        # init graph db instance
        logging.info('Initializing neo4j connection...')
        self._graph_ref = GraphReference()
        
        # set up a web socket server
        logging.info('Initializing websocket server at %s:%s ...', SOCKET_CONF['host'], SOCKET_CONF['port'])
        self._server = Server((SOCKET_CONF['host'], SOCKET_CONF['port'])).register(self)  

        Worker(process=False).register(self)
        Static().register(self._server)
        Logger().register(self._server)
        
        if debug:
            Debugger(events=False).register(self)

        self._ws = WebSocket().register(self._server)
        WebSocketsDispatcher("/simengine").register(self._server)

        ### Register Assets ###
        self._subscribe_to_channels()
        self._reload_model(force_snmp_init)
       

    def _subscribe_to_channels(self):
        """Subscribe to redis channels"""
        
        logging.info('Initializing redis subscriptions...')

        # State Channels
        self._state_pubsub.psubscribe(
            RedisChannels.oid_update_channel,  # snmp oid updates
            RedisChannels.state_update_channel, # power state changes
            RedisChannels.mains_update_channel, # wall power updates
            RedisChannels.model_update_channel  # model changes
        )

        # Battery Channel
        self._bat_pubsub.psubscribe(
            RedisChannels.battery_update_channel, # battery level updates
            RedisChannels.battery_conf_drain_channel, # update drain speed (factor)
            RedisChannels.battery_conf_charge_channel # update charge speed (factor)
        )

        # Thermal Channels
        self._thermal_pubsub.psubscribe(
            RedisChannels.ambient_update_channel, # on ambient changes
            RedisChannels.sensor_conf_th_channel, # new relationship
            RedisChannels.cpu_usg_conf_th_channel, # new cpu-usage relationship
        )


    def _reload_model(self, force_snmp_init=True):
        """Re-create system topology (instantiate assets based on graph ref)"""

        logging.info('Initializing system topology...')

        self._assets = {}

        # init state
        clear_temp()
        initialize(force_snmp_init) 

        # instantiate assets based on graph records
        leaf_nodes = []

        with self._graph_ref.get_session() as session:
            assets = GraphReference.get_assets_and_children(session)
            for asset in assets:
                try:
                    self._assets[asset['key']] = Asset.get_supported_assets()[asset['type']](asset).register(self)
                    
                    # leaf nodes will trigger load updates
                    if not asset['children']:
                        leaf_nodes.append(asset['key'])

                except StopIteration:
                    logging.error('Detected asset that is not supported')

        # initialize load by dispatching load update
        for key in leaf_nodes:
            asset_key = int(key)
            new_load = self._assets[key].state.power_usage

            # notify parents of load changes
            self._chain_load_update( 
                LoadEventResult(
                    load_change=new_load,
                    new_load=new_load,
                    old_load=0,
                    asset_key=asset_key
                )
            )

            # update websocket
            self._notify_client(ClientRequests.asset, {
                'key': asset_key, 
                'load': new_load
            })
            
        StateManager.set_ambient(21)
        #self._handle_ambient_update(new_temp=StateManager.get_ambient(), old_temp=0)


    def _handle_oid_update(self, asset_key, oid, value):
        """React to OID update in redis store 
        Args:
            asset_key(int): key of the asset oid belongs to
            oid(str): updated oid
            value(str): OID value in snmpsim format "datatype|value"
        """
        if asset_key not in self._assets:
            return

        oid = oid.replace(" ", "")
        _, oid_value = value.split("|")
        with self._graph_ref.get_session() as session:
            affected_keys, oid_details = GraphReference.get_asset_oid_info(session, asset_key, oid)
            
            oid_value_name = oid_details['specs'][oid_value]
            oid_name = oid_details['name']

            for key in affected_keys:
                self.fire(PowerEventManager.get_state_specs()[oid_name][oid_value_name], self._assets[key])

        logging.info('oid changed:')
        logging.info(">" + oid + ": " + oid_value)
        

    def _handle_ambient_update(self, new_temp, old_temp):
        """React to ambient update by notifying all the assets in the sys topology
        Args:
            new_temp(float): new ambient value
            old_temp(float): old ambient value
        """

        self._notify_client(ClientRequests.ambient, {'ambient': new_temp, 'rising': new_temp > old_temp})
        for a_key in self._assets:
            self.fire(PowerEventManager.map_ambient_event(old_temp, new_temp), self._assets[a_key]) 

    

    def _handle_state_update(self, asset_key):
        """React to asset state updates in redis store 
        Args:
            asset_key(int): key of the updated asset
        """
        
        updated_asset = self._assets[int(asset_key)]
        asset_status = str(updated_asset.state.status)

        # write to a web socket
        self._notify_client(ClientRequests.asset, {
            'key': asset_key, 
            'status':  int(asset_status)
        })

        # fire-up power events down the power stream
        self.fire(PowerEventManager.map_asset_event(asset_status), updated_asset)
        self._chain_power_update(PowerEventResult(asset_key=asset_key, new_state=asset_status))


    def _chain_load_update(self, event_result, increased=True):
        """React to load update event by propogating the load changes up the power stream
        
        Args:
            event_result(LoadEventResult): contains data about load update event such as key of 
                                           the affected asset, its old load, new load and load change 
            increased(bool): true if load was incresed

        Example:
            when a leaf node is powered down, its load is set to 0 -> parent assets get updated load values
        """
        load_change = event_result.load_change 
        child_key = int(event_result.asset_key)
        
        if not load_change:
            return

        with self._graph_ref.get_session() as session:
            parent_assets = GraphReference.get_parent_assets(session, child_key)

            for parent_info in parent_assets:
                parent = self._assets[parent_info['key']]
                child = self._assets[child_key]

                # load was already updated for ups parent
                if child.state.asset_type == 'ups' and not parent.state.status:
                    return

                parent_load_change = load_change * parent.state.draw_percentage
                # logging.info(
                #     "child [%s] load update: %s; updating %s load for [%s]", 
                # child_key, load_change, parent.state.load, parent.key
                # )
               
                if increased:
                    event = PowerEventManager.map_load_increased_by(parent_load_change, child_key)
                else: 
                    event = PowerEventManager.map_load_decreased_by(parent_load_change, child_key)
                self.fire(event, parent)
    
    
    def _chain_power_update(self, event_result):
        """React to power state event by analysing the parent, child & neighbouring assets
        
        Args:
            event_result(PowerEventResult): contains data about power state update event such as key of 
                                           the affected asset, its old state & new state
        Example:
            when a node is powered down, the assets it powers should be powered down as well
        """
        asset_key = int(event_result.asset_key)
        new_state = int(event_result.new_state)

        with self._graph_ref.get_session() as session:
            children, parent_assets, _2nd_parent = GraphReference.get_affected_assets(session, asset_key)
            updated_asset = self._assets[asset_key]

            # Meaning it's a leaf node -> update load up the power chain if needed
            if not children and parent_assets:
                offline_parents_load = 0
                online_parents = []

                for parent_info in parent_assets:
                    parent = self._assets[parent_info['key']]
                    parent_load_change = updated_asset.state.power_usage * parent.state.draw_percentage

                    if not parent.state.load and not parent.state.status:
                        # if offline -> find how much power parent should draw 
                        # (so it will be redistributed among other assets)
                        offline_parents_load += parent_load_change
                    else:
                        online_parents.append(parent.key)

                # for each parent that is either online or it's load is not zero
                # update the load value
                for parent_key in online_parents:

                    parent_asset = self._assets[parent_key]
                    leaf_node_amp = updated_asset.state.power_usage * parent_asset.state.draw_percentage

                    if new_state == 0:
                        event = PowerEventManager.map_load_decreased_by(offline_parents_load + leaf_node_amp, asset_key)
                    else:
                        event = PowerEventManager.map_load_increased_by(offline_parents_load + leaf_node_amp, asset_key)

                    self.fire(event, parent_asset)

                if new_state == 0:
                    updated_asset.state.update_load(0)


            # Check assets down the power stream (assets powered by the updated asset)
            for child in children:
                child_asset = self._assets[child['key']]
                second_parent_up = False
                second_parent_asset = None

                # check if there's an alternative power source of the child asset
                '''
                 e.g.
                 (psu1)  (psu2)
                   \       /
                  [pow]  [pow]
                     \   /
                     (server) <- child
                '''
                if _2nd_parent:
                    second_parent_asset = self._assets[int(_2nd_parent['key'])]
                    second_parent_up = second_parent_asset.state.status
                
                # power up/down child assets if there's no alternative power source
                if not second_parent_up:
                    event = PowerEventManager.map_parent_event(str(new_state))
                    self.fire(event, child_asset)

                    # Special case for UPS
                    if child_asset.state.asset_type == 'ups' and child_asset.state.battery_level:
                        node_load = child_asset.state.load * updated_asset.state.draw_percentage

                        # ups won't be powered off but the load has to change anyways
                        if not new_state:
                            load_upd = PowerEventManager.map_load_decreased_by(node_load, child_asset.key)
                        else:
                            load_upd = PowerEventManager.map_load_increased_by(node_load, child_asset.key)

                        self.fire(load_upd, updated_asset)


                # check upstream & branching power
                # alternative power source is available, therefore the load needs to be re-directed
                else:
                    logging.info('Asset[%s] has alternative parent[%s]', child_asset.key, second_parent_asset.key)

                    # find out how much load the 2nd parent should take
                    # (how much updated asset was drawing)
                    node_load = child_asset.state.load * updated_asset.state.draw_percentage

                    # logging.info('Child load : {}'.format(node_load))
                    if int(new_state) == 0:  
                        alt_branch_event = PowerEventManager.map_load_increased_by(node_load, child_asset.key)             
                    else:
                        alt_branch_event = PowerEventManager.map_load_decreased_by(node_load, child_asset.key)
                    
                    # increase power on the neighbouring power stream 
                    self.fire(alt_branch_event, second_parent_asset)

                    # change load up the node path that powers the updated asset
                    event = PowerEventManager.map_child_event(str(new_state), node_load, asset_key)
                    self.fire(event, updated_asset)


    def _notify_client(self, client_request, data):
        """Notify the WebSocket client(s) of any changes in asset states 

        Args:
            client_request(ClientRequests): type of data passed to the ws client
            data(dict): updated key/values (e.g. status, load)
        """

        self.fire(NotifyClient({
            'request': client_request.name,
            'data': data
        }), self._ws)


    def monitor_battery(self):
        """Monitor battery in a separate pub/sub stream"""
        message = self._bat_pubsub.get_message()

        # validate message
        if ((not message) or ('data' not in message) or (not isinstance(message['data'], bytes))):
            return
        
        data = message['data'].decode("utf-8")
        channel = message['channel'].decode()
        
        try:
            logging.info("[REDIS:BATTERY] Received a message in channel [%s]: %s", channel, data)

            if channel == RedisChannels.battery_update_channel:
                asset_key, _ = data.split('-')
                self._notify_client(ClientRequests.asset, {
                    'key': int(asset_key),
                    'battery': self._assets[int(asset_key)].state.battery_level
                })
                
            elif channel == RedisChannels.battery_conf_charge_channel:
                asset_key, _ = data.split('-')
                _, speed = data.split('|')
                self._assets[int(asset_key)].charge_speed_factor = float(speed)
            elif channel == RedisChannels.battery_conf_drain_channel:
                asset_key, _ = data.split('-')
                _, speed = data.split('|')
                self._assets[int(asset_key)].drain_speed_factor = float(speed)


        except KeyError as error:
            logging.error("Detected unregistered asset under key [%s]", error)


    def monitor_state(self):
        """ listens to redis events """

        message = self._state_pubsub.get_message()

        # validate message
        if ((not message) or ('data' not in message) or (not isinstance(message['data'], bytes))):
            return
        
        data = message['data'].decode("utf-8")

        # interpret the published message 
        # "state-upd" indicates that certain asset was powered on/off by the interface(s)
        # "oid-upd" is published when SNMPsim updates an OID
        channel = message['channel'].decode()

        try:

            logging.info("[REDIS:POWER] Received a message in channel [%s]: %s", channel, data)

            if channel == RedisChannels.state_update_channel:
                asset_key, asset_type = data.split('-')
                if asset_type in Asset.get_supported_assets():
                    self._handle_state_update(int(asset_key))
            
            elif channel == RedisChannels.mains_update_channel:
        
                with self._graph_ref.get_session() as session:
                    mains_out_keys = GraphReference.get_mains_powered_outlets(session)
                    mains_out = {out_key: self._assets[out_key] for out_key in mains_out_keys if out_key}
          
                    new_state = int(data)

                    self._notify_client(ClientRequests.mains, {'mains': new_state})     
                    self.fire(PowerEventManager.map_mains_event(data), self._sys_environ)

                    for _, outlet in mains_out.items():
                        if new_state == 0:
                            outlet.state.shut_down() 
                        else:
                            outlet.state.power_up()

                        outlet.state.publish_power()

            elif channel == RedisChannels.oid_update_channel:
                value = (self._redis_store.get(data)).decode()
                asset_key, oid = data.split('-')
                self._handle_oid_update(int(asset_key), oid, value)

            elif channel == RedisChannels.model_update_channel:
                self._state_pubsub.unsubscribe()
                self._bat_pubsub.unsubscribe()

                self._reload_model()
                self._subscribe_to_channels()

        except KeyError as error:
            logging.error("Detected unregistered asset under key [%s]", error)


    def monitor_thermal(self):
        """Monitor thermal updates in a separate pub/sub channel"""

        message = self._thermal_pubsub.get_message()

        # validate message
        if ((not message) or ('data' not in message) or (not isinstance(message['data'], bytes))):
            return
        
        data = message['data'].decode("utf-8")
        channel = message['channel'].decode()

        try:
            logging.info("[REDIS:THERMAL] Received a message in channel [%s]: %s", channel, data)

            if channel == RedisChannels.ambient_update_channel:
                old_temp, new_temp = map(float, data.split('-'))
                self._handle_ambient_update(new_temp=float(new_temp), old_temp=old_temp)
            elif channel == RedisChannels.sensor_conf_th_channel:
                new_rel = json.loads(data)
                self._assets[new_rel['key']].add_sensor_thermal_impact(**new_rel['relationship'])
            elif channel == RedisChannels.cpu_usg_conf_th_channel:
                new_rel = json.loads(data)
                self._assets[new_rel['key']].add_cpu_thermal_impact(**new_rel['relationship'])

        except KeyError as error:
            logging.error("Detected unregistered asset under key [%s]", error)


    def started(self, *args):
        """
            Called on start
        """
        logging.info('Initializing pub/sub event handlers...')
        Timer(0.5, Event.create("monitor_state"), persist=True).register(self)
        Timer(1, Event.create("monitor_battery"), persist=True).register(self)
        Timer(1, Event.create("monitor_thermal"), persist=True).register(self)


    # **Events are camel-case
    # pylint: disable=C0103,W0613

    ############### Load Events - Callbacks (called only on success)

    def _load_success(self, event_result, increased=True):
        """Handle load event changes by dispatching load update events up the power stream"""
        self._chain_load_update(event_result, increased)
        if event_result.load_change:
            ckey = int(event_result.asset_key)
            self._notify_client(ClientRequests.asset, {'key': ckey, 'load': self._assets[ckey].state.load})

    # Notify parent asset of any child events
    def ChildAssetPowerDown_success(self, evt, event_result):
        """When child is powered down -> get the new load value of child asset"""
        self._load_success(event_result, increased=False)
        
    def ChildAssetPowerUp_success(self, evt, event_result):
        """When child is powered up -> get the new load value of child asset"""       
        self._load_success(event_result, increased=True)

    def ChildAssetLoadDecreased_success(self, evt, event_result):
        """When load decreases down the power stream """       
        self._load_success(event_result, increased=False)

    def ChildAssetLoadIncreased_success(self, evt, event_result):
        """When load increases down the power stream """        
        self._load_success(event_result, increased=True)


    ############### Power Events - Callbacks 

    def _power_success(self, event_result):
        """Handle power event success by dispatching power events down the power stream"""
        self._notify_client(ClientRequests.asset, {
            'key': event_result.asset_key, 
            'status': int(event_result.new_state)
        })
        self._chain_power_update(event_result)
    
     # Notify child asset of any parent events of interest
    def ParentAssetPowerDown_success(self, evt, event_result):
        """When assets parent successfully powered down """
        self._power_success(event_result)

    def ParentAssetPowerUp_success(self, evt, event_result):
        """When assets parent successfully powered up """
        self._power_success(event_result)

    def SignalDown_success(self, evt, event_result):
        """When asset is powered down """
        self._power_success(event_result)

    def SignalUp_success(self, evt, event_result):
        """When asset is powered up """
        self._power_success(event_result)

    def SignalReboot_success(self, evt, e_result):
        """Rebooted """

        # need to do power chain
        if not e_result.old_state and e_result.old_state != e_result.new_state:
            self._chain_power_update(e_result)

        self._notify_client(ClientRequests.asset, {
            'key': e_result.asset_key, 
            'status': e_result.new_state
        })

if __name__ == '__main__':
    StateListener().run()
