""" StateListener monitors any updates to assets/OIDs """

from circuits import Component, Event, Timer, Worker
import redis
import sys

from state.assets import PDU, Outlet, Asset
from state.event_map import event_map
from state.asset_types import ASSET_TYPES
from state.graph_reference import get_db

class StateListener(Component):
    """ Top-level component """

    def __init__(self):
        super(StateListener, self).__init__()

        # subscribe to redis key events
        self.redis_store = redis.StrictRedis(host='localhost', port=6379)
        self.pubsub = self.redis_store.pubsub()
        self.pubsub.psubscribe('__key*__:*')
        self._assets = []
        
        self._graph_db = get_db()
        results = self._graph_db.run(
            "MATCH (asset:Asset) return asset"
        )

        supports_asset = lambda x: x.lower() if x.lower() in ASSET_TYPES else None

        for record in results:
            asset_types = filter(supports_asset, record['asset'].labels)
            try:
                self._assets.append(
                    self.map_assets(next(iter(asset_types)).lower(), record['asset'].get('key'))
                )
            except KeyError:
                print('Asset may not be supported')

        Worker(process=False).register(self)


    def map_assets(self, asset, key):
        return { # TODO: https://stackoverflow.com/questions/30654328/python-create-object-from-string
            'pdu': PDU(key).register(self),
            'outlet': Outlet(key).register(self),
            'switch': Asset(key).register(self)
        }[asset]


    def monitor(self):
        """ listens to redis events """

        print("...")
        message = self.pubsub.get_message() 

        # validate message
        if ((not message) or ('data' not in message) or (not isinstance(message['data'], bytes))):
            return

        data = message['data'].decode("utf-8")
        value = (self.redis_store.get(data)).decode()

        # lookup asset
        asset_key, property_id = data.split('-')
        if property_id in ASSET_TYPES:

            # loop up child nodes
            results = self._graph_db.run(
                "MATCH (asset:Asset)-[:POWERED_BY]->({ key: $key }) return asset",
                key=int(asset_key)
            )

            for record in results:
                key = record['asset'].get('key')

                for asset in self._assets:
                    if asset.get_key() == key:
                        print(asset)
                        print(event_map[property_id][value])
                        self.fire(event_map[property_id][value], asset)

            print("Key: {}-{} -> {}".format(asset_key, property_id.replace(" ", ""), value))


    def started(self, *args):
        """
            Called on start
        """
        print('Listening to Redis events')
        # check redis state every second
        Timer(1, Event.create("monitor"), persist=True).register(self)

if __name__ == '__main__':
    StateListener().run()
