""" StateListener monitors any updates to assets/OIDs """
import sys

from circuits import Component, Event, Timer, Worker, Debugger, task
import redis

from circuits.web import Logger, Server, Static
from circuits.web.dispatchers import WebSocketsDispatcher

from enginecore.state.assets import Asset, PowerEventResult, LoadEventResult
from enginecore.state.utils import get_asset_type
from enginecore.state.event_map import PowerEventManager
from enginecore.model.graph_reference import GraphReference
from enginecore.state.web_socket import WebSocket


class NotifyClient(Event):
    """Notify websocket clients of any data updates"""

class StateListener(Component):
    """Top-level component that instantiates assets & maps redis events to circuit events"""


    def __init__(self, debug=False):
        super(StateListener, self).__init__()

        # subscribe to redis key events
        self.redis_store = redis.StrictRedis(host='localhost', port=6379)
        self.pubsub = self.redis_store.pubsub()
        self.pubsub.psubscribe('oid-upd', 'state-upd')

        # assets will store all the devices/items including PDUs, switches etc.
        self._assets = {}
        self._graph_ref = GraphReference()
        self._graph_db = self._graph_ref.get_session()
        
        # set up a web socket
        self._server = Server(("0.0.0.0", 8000)).register(self)     
        # Worker(process=False).register(self)
        Static().register(self._server)
        Logger().register(self._server)
        
        if debug:
            Debugger(events=False).register(self)

        self._ws = WebSocket().register(self._server)
    
        WebSocketsDispatcher("/simengine").register(self._server)

        # query graph db for the nodes labeled as `Asset`
        results = self._graph_ref.get_session().run(
            "MATCH (asset:Asset) OPTIONAL MATCH (asset)<-[:POWERED_BY]-(childAsset:Asset) return asset, collect(childAsset) as children ORDER BY asset.key ASC"
        )

        # instantiate assets based on graph records
        leaf_nodes = []
        for record in results:
            try:
                asset_type = get_asset_type(record['asset'].labels)
                asset_key = record['asset'].get('key')
                self._assets[asset_key] = Asset.get_supported_assets()[asset_type](dict(record['asset'])).register(self)
                if not record['children']:
                    leaf_nodes.append(asset_key) 
            except StopIteration:
                print('Detected asset that is not supported', file=sys.stderr)

        for key in leaf_nodes:
            self._chain_load_update( 
                LoadEventResult(
                    load_change=self._assets[key].get_amperage(),
                    asset_key=key
                )
            )



    def _handle_oid_update(self, asset_key, oid, value):
        if int(asset_key) not in self._assets:
            return

        oid = oid.replace(" ", "")
        _, oid_value = value.split("|")

        # look up dependant nodes
        results = self._graph_ref.get_session().run(
            'MATCH (asset:Asset)-[:POWERED_BY]->(oid:OID { OID: $oid })<-[:HAS_OID]-({key: $key}) \
                MATCH (oid)-[:HAS_STATE_DETAILS]->(oid_specs) \
            return asset, oid, oid_specs',
            oid=oid,key=int(asset_key)
        )

        for record in results:
            key = record['asset'].get('key')
            oid_name = record['oid']['OIDName']
            oid_value_name = dict(record['oid_specs'])[oid_value]

            self.fire(PowerEventManager.get_state_specs()[oid_name][oid_value_name], self._assets[key])

        print('oid changed:')
        print(">" + oid + ": " + oid_value)
        
    
    def _handle_state_update(self, asset_key, asset_type):
        
        
        if asset_type not in Asset.get_supported_assets():
            return
        
        updated_asset = self._assets[int(asset_key)]
        asset_status = str(updated_asset.status())
        asset_info = PowerEventResult(asset_key=asset_key, asset_type=asset_type, new_state=asset_status)

        self._notify_client(asset_info)
        self.fire(PowerEventManager.map_asset_event(asset_status), updated_asset)
        self._chain_power_update(asset_info)
            
        print("Key: {}-{} -> {}".format(asset_key, asset_type, asset_status))


    def monitor(self):
        """ listens to redis events """

        print("...")
        message = self.pubsub.get_message()

        # validate message
        if ((not message) or ('data' not in message) or (not isinstance(message['data'], bytes))):
            return
        
        data = message['data'].decode("utf-8")

        # interpret the published message 
        # "state-upd" indicates that certain asset was powered on/off by the interface(s)
        # "oid-upd" is published when SNMPsim updates an OID
        try:
            if message['channel'] == b"state-upd":
                asset_key, asset_type = data.split('-')
                self._handle_state_update(asset_key, asset_type)
            elif message['channel'] == b"oid-upd":
                value = (self.redis_store.get(data)).decode()
                asset_key, oid = data.split('-')
                self._handle_oid_update(asset_key, oid, value)

        except KeyError as error:
            print("Detected unregistered asset under key [{}]".format(error), file=sys.stderr)


    def get_assets(self):
        """running instances """
        return self._assets


    def started(self, *args):
        """
            Called on start
        """
        print('Listening to Redis events')
        Timer(0.5, Event.create("monitor"), persist=True).register(self)


    def __exit__(self, exc_type, exc_value, traceback):
        self._graph_db.close()


    def _chain_load_update(self, event_result, increased=True):

        load_change = event_result.load_change 
        child_key = event_result.asset_key

        results = self._graph_db.run(
            "MATCH (:Asset { key: $key })-[:POWERED_BY]->(asset:Asset) RETURN asset",
            key=int(child_key)
        )

 
        if results and load_change:
            for record in results:
                parent_asset = dict(record['asset'])
                parent_load = self._assets[parent_asset['key']].get_load()
                new_load = load_change * self._assets[parent_asset['key']].get_draw_percentage()
                print("-- child [{}] power/load update as '{}', updating load for [{}], parent_load: {}".format(child_key, load_change, parent_asset['key'], parent_load))
                
                if increased:
                    event = PowerEventManager.map_load_increased_by(new_load, child_key)
                else: 
                    event = PowerEventManager.map_load_decreased_by(new_load, child_key)
                
                #if parent_load:
                self.fire(event, self._assets[parent_asset['key']])

        if load_change:
            # Notify web-socket client of a load update
            self.fire(NotifyClient({ # TODO: refactor
                'key': int(child_key),
                'data': {
                    'load': self._assets[int(child_key)].get_load()
            }}), self._ws)

    
    def _chain_power_update(self, event_result):
        asset_key = event_result.asset_key
        new_state = event_result.new_state

        # look up child nodes & parent node
        results = self._graph_db.run(
            "OPTIONAL MATCH  (parentAsset:Asset)<-[:POWERED_BY]-(assetOff { key: $key }) "
            "OPTIONAL MATCH (nextAsset:Asset)-[:POWERED_BY]->({ key: $key }) "
            "OPTIONAL MATCH (nextAsset2ndParent)<-[:POWERED_BY]-(nextAsset) WHERE assetOff.key <> nextAsset2ndParent.key "
            "RETURN collect(nextAsset) as childAssets,  collect(parentAsset) as parentAsset, nextAsset2ndParent, count(parentAsset) as num_parents",
            key=int(asset_key)
        )


        for record in results:

            # Meaning it's a leaf node -> update load up the power chain if needed
            if not record['childAssets'] and record['parentAsset']:
        
                offline_parents_load = 0
                online_parents = []

                for parent in record['parentAsset']:
                    parent_key = int(parent.get('key'))
                    leaf_node_amp = self._assets[int(asset_key)].get_amperage() * self._assets[parent_key].get_draw_percentage()

                   #  print('parent up/down: {}'.format(self._assets[parent_key].status()))
                    if not self._assets[parent_key].get_load() and not self._assets[parent_key].status():
                        # if offline -> find how much power parent should draw 
                        # (so it will be redistributed among other assets)
                        offline_parents_load += leaf_node_amp
                    else:
                        online_parents.append(parent_key)

                # for each parent that is either online of it's load is not zero
                for parent_key in online_parents:
                    # print("++ for parent-[{}], new load is {} by {}", parent_key, (offline_parents_load + leaf_node_amp), 'increased' if int(new_state) == 0 else 'decreased') 
                    leaf_node_amp = self._assets[int(asset_key)].get_amperage() * self._assets[parent_key].get_draw_percentage()
                    if int(new_state) == 0:
                        event = PowerEventManager.map_load_decreased_by(offline_parents_load + leaf_node_amp, int(asset_key))
                    else:
                        event = PowerEventManager.map_load_increased_by(offline_parents_load + leaf_node_amp, int(asset_key))

                    self.fire(event, self._assets[parent_key])

                if int(new_state) == 0:
                    self._assets[int(asset_key)].get_state().update_load(0)

            # Check assets down the power stream
            for child in record['childAssets']:
                child_key = child.get('key')
                second_parent_up = False
                second_parent = False
                # check if there's an alternative power source of the child asset
                '''
                 e.g.
                 (psu1)  (psu2)
                   \       /
                  [pow]  [pow]
                     \   /
                     (server) <- child
                '''
                if record['nextAsset2ndParent']:
                    second_parent = record['nextAsset2ndParent']
                    second_parent_up = self._assets[int(second_parent.get('key'))].status()
                
                # power up/down child assets if there's no alternative power source
                if not second_parent_up:
                    event = PowerEventManager.map_parent_event(str(new_state))
                    node_load = self._assets[child_key].get_load()
                    self.fire(event, self._assets[child_key])

                # check upstream & branching power
                # alternative power source is available, therefore the load needs to be re-directed
                if second_parent_up:
                    print('Found an asset that has alternative parent[{}], child[{}]'.format(second_parent.get('key'), child_key))
                    # find out how much load the 2nd parent should take
                    # (how much updated asset was drawing)
                    node_load = self._assets[child_key].get_load() * self._assets[int(asset_key)].get_draw_percentage()

                    print('Child load : {}'.format(node_load))
 
                    if int(new_state) == 0:  
                        alt_branch_event = PowerEventManager.map_load_increased_by(node_load, child_key)             
                    else:
                        alt_branch_event = PowerEventManager.map_load_decreased_by(node_load, child_key)
                    
                    # increase power on the neighbouring power stream 
                    self.fire(alt_branch_event, self._assets[int(second_parent.get('key'))])
                    # change load up the node path that powers the updated asset
                    event = PowerEventManager.map_child_event(str(new_state), node_load, asset_key)
                    self.fire(event, self._assets[int(asset_key)])
                    

    def _notify_client(self, event_result):
        asset_key = event_result.asset_key
        state = event_result.new_state

        self.fire(NotifyClient({
            'key': int(asset_key),
            'data': {
                'status': int(state)
        }}), self._ws)

    # Events are camel-case
    # pylint: disable=C0103

    # Notify parent asset of any child events
    def ChildAssetPowerDown_success(self, evt, event_result):
        """ When child is powered down -> get the new load value of child asset"""
        self._chain_load_update(event_result, increased=False)
        
    def ChildAssetPowerUp_success(self, evt, event_result):
        """ When child is powered up -> get the new load value of child asset"""        
        self._chain_load_update(event_result)

    def ChildAssetLoadDecreased_success(self, evt, event_result):
        """ When load decreases down the power stream """        
        self._chain_load_update(event_result, increased=False)

    def ChildAssetLoadIncreased_success(self, evt, event_result):
        """ When load increases down the power stream """        
        self._chain_load_update(event_result)


    # Notify child asset of any parent events of interest
    def ParentAssetPowerDown_success(self, evt, event_result):
        """ When assets parent successfully powered down """
        self._notify_client(event_result)
        self._chain_power_update(event_result)

    def ParentAssetPowerUp_success(self, evt, event_result):
        """ When assets parent successfully powered up """
        self._notify_client(event_result)
        self._chain_power_update(event_result)

    def SignalDown_success(self, evt, event_result):
        """ When asset is powered down """
        self._notify_client(event_result)
        self._chain_power_update(event_result)

    def SignalUp_success(self, evt, event_result):
        """ When asset is powered up """
        self._notify_client(event_result)
        self._chain_power_update(event_result)

    def SignalReboot_success(self, evt, e_result):
        """ Rebooted """

        # need to do power chain
        if not e_result.old_state and e_result.old_state != e_result.new_state:
            self._chain_power_update(e_result)

        self._notify_client(e_result)

if __name__ == '__main__':
    StateListener().run()
