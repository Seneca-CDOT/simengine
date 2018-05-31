""" StateListener monitors any updates to assets/OIDs """
import sys

from circuits import Component, Event, Timer, Worker
import redis

from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.event_map import event_map
from enginecore.state.graph_reference import GraphReference

class StateListener(Component):
    """ Top-level component that instantiates assets & maps redis events to circuit events"""


    def __init__(self):
        super(StateListener, self).__init__()

        # subscribe to redis key events
        self.redis_store = redis.StrictRedis(host='localhost', port=6379)
        self.pubsub = self.redis_store.pubsub()
        self.pubsub.psubscribe('__key*__:*')

        # assets will store all the devices/items including PDUs, switches etc.
        self._assets = []
        self._graph_db = GraphReference().get_session()

        # query graph db for the nodes labeled as `Asset`
        results = self._graph_db.run(
            "MATCH (asset:Asset) return asset"
        )

        # instantiate assets based on graph records
        for record in results:
            try:
                asset_label = set(SUPPORTED_ASSETS).intersection(
                    map(lambda x: x.lower(), record['asset'].labels)
                )

                asset_key = record['asset'].get('key')

                self._assets.append(
                    SUPPORTED_ASSETS[next(iter(asset_label), '').lower()](asset_key).register(self)
                )

            except KeyError:
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

        updated_asset = list(filter(lambda x: x.get_key() == int(asset_key), self._assets))
        self.fire(event_map[property_id][value], next(iter(updated_asset)))

        if property_id in SUPPORTED_ASSETS:

            # loop up child nodes
            results = self._graph_db.run(
                "MATCH (asset:Asset)-[:POWERED_BY]->({ key: $key }) return asset",
                key=int(asset_key)
            )

            for record in results:
                key = record['asset'].get('key')

                for asset in self._assets:
                    if asset.get_key() == key:
                        # print(asset.get_key())
                        # print(event_map[property_id][value])
                        self.fire(event_map[property_id][value], asset)

            print("Key: {}-{} -> {}".format(asset_key, property_id.replace(" ", ""), value))


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

if __name__ == '__main__':
    StateListener().run()
