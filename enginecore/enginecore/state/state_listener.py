""" StateListener monitors any updates to assets/OIDs """
import sys

from circuits import Component, Event, Timer, Worker, Debugger
import redis

from circuits.web import Logger, Server, Static
from circuits.web.dispatchers import WebSocketsDispatcher

from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.utils import get_asset_type
from enginecore.state.event_map import PowerEventManager
from enginecore.state.graph_reference import GraphReference
from enginecore.state.web_socket import WebSocket


class NotifyClient(Event):
    """Notify websocket clients of any data updates"""

class StateListener(Component):
    """ Top-level component that instantiates assets & maps redis events to circuit events"""


    def __init__(self):
        super(StateListener, self).__init__()

        # subscribe to redis key events
        self.redis_store = redis.StrictRedis(host='localhost', port=6379)
        self.pubsub = self.redis_store.pubsub()
        self.pubsub.psubscribe('__key*__:*')

        # assets will store all the devices/items including PDUs, switches etc.
        self._assets = {}
        self._graph_db = GraphReference().get_session()
        
        # set up a web socket
        self._server = Server(("0.0.0.0", 8000)).register(self)     
        Static().register(self._server)
        Logger().register(self._server)
        # Debugger().register(self._server)
        self._ws = WebSocket().register(self._server)
    
        WebSocketsDispatcher("/simengine").register(self._server)

        # query graph db for the nodes labeled as `Asset`
        results = self._graph_db.run(
            "MATCH (asset:Asset) return asset"
        )

        # instantiate assets based on graph records
        for record in results:
            try:
                asset_type = get_asset_type(record['asset'].labels)
                asset_key = record['asset'].get('key')
                self._assets[asset_key] = SUPPORTED_ASSETS[asset_type](dict(record['asset'])).register(self)     

            except StopIteration:
                print('Detected asset that is not supported', file=sys.stderr)

        Worker(process=False).register(self)


    def monitor(self):
        """ listens to redis events """

        print("...")
        message = self.pubsub.get_message()

        # validate message
        if ((not message) or ('data' not in message) or (not isinstance(message['data'], bytes))):
            return

        data = message['data'].decode("utf-8")
        value = (self.redis_store.get(data)).decode()
        asset_key, property_id = data.split('-')

        try:

            if property_id in SUPPORTED_ASSETS:

                updated_asset = self._assets[int(asset_key)]
                asset_info = (asset_key, property_id, value)
                self._notify_client(asset_info)

                self.fire(PowerEventManager.map_asset_event(value), updated_asset)

                # look up child nodes
                results = self._graph_db.run(
                    "MATCH (asset:Asset)-[r:POWERED_BY]-({ key: $key }) return asset,(startNode(r) = asset) as powers",
                    key=int(asset_key)
                )

                for record in results:
                   
                    key = record['asset'].get('key')

                    # 'powers' is true if the updated asset powers the dependant assets
                    # 'powers' is false if the updated asset is powered by the connected asset
                    if record['powers']: 
                        event = PowerEventManager.map_parent_event(value)
                    else:
                        event = PowerEventManager.map_child_event(value, asset_key)
                    
                    self.fire(event, self._assets[key])
                        

                print("Key: {}-{} -> {}".format(asset_key, property_id.replace(" ", ""), value))


            elif int(asset_key) in self._assets:
               
                oid = property_id.replace(" ", "")
                _, oid_value = value.split("|")

                # look up dependant nodes
                results = self._graph_db.run(
                    'MATCH (asset:Asset)-[:POWERED_BY]->(oid:OID { OID: $oid }) \
                     MATCH (oid)-[:HAS_STATE_DETAILS]->(oid_specs) \
                    return asset, oid, oid_specs',
                    oid=oid
                )

                for record in results:
                    key = record['asset'].get('key')
                    oid_name = record['oid']['OIDName']
                    oid_value_name = dict(record['oid_specs'])[oid_value]
                    # print(oid_name)
                    # print(oid_value_name)
                    # print(PowerEventManager.get_state_specs()[oid_name][oid_value_name])

                    self.fire(PowerEventManager.get_state_specs()[oid_name][oid_value_name], self._assets[key])

                print('oid changed:')
                print(">" + oid + ": " + oid_value)
               

        except KeyError as error:
            print("Detected unregistered asset under key [{}]".format(error), file=sys.stderr)


    def get_assets(self):
        """ running instances """
        return self._assets


    def started(self, *args):
        """
            Called on start
        """
        print('Listening to Redis events')
        # check redis state every second
        Timer(1, Event.create("monitor"), persist=True).register(self)

    def __exit__(self, exc_type, exc_value, traceback):
        self._graph_db.close()


    def _chain_load_update(self, event_result):

        new_load, child_key = event_result

        results = self._graph_db.run(
            "MATCH (:Asset { key: $key })-[:POWERED_BY]->(asset:Asset) RETURN asset",
            key=int(child_key)
        )

        record = results.single()
        if record:
            parent_asset = dict(record['asset'])
            if self._assets[child_key].status():
                print("-- child [{}] power/load update as '{}', updating load for [{}]".format(child_key, new_load, parent_asset['key']))
                self.fire(PowerEventManager.map_load_event(new_load, child_key), self._assets[parent_asset['key']])

        # Notify web-socket client of a load update
        self.fire(NotifyClient({ 
            'key': int(child_key),
            'data': {
                'load': new_load
        }}), self._ws)


    def _notify_client(self, data):

        asset_key, asset_type, state = data

        self.fire(NotifyClient({  ## TODO: Move this into '_success' function
            'key': int(asset_key),
            'data': {
                'type':  asset_type,
                'status': int(state)
        }}), self._ws)


    def ChildAssetPowerDown_success(self, evt, event_result):
        """ When child is powered down -> get the new load value of child asset"""
        self._chain_load_update(event_result)
        

    def ChildAssetPowerUp_success(self, evt, event_result):
        """ When child is powered up -> get the new load value of child asset"""        
        self._chain_load_update(event_result)


    def LoadUpdate_success(self, evt, event_result):
        """ When load changes down the power stream -> get the new load value of child asset """        
        self._chain_load_update(event_result)
    

    def ParentAssetPowerDown_success(self, evt, event_result):
        self._notify_client(event_result)


    def ParentAssetPowerUp_success(self, evt, event_result):
        self._notify_client(event_result)

if __name__ == '__main__':
    StateListener().run()
