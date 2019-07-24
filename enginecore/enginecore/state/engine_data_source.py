import functools
from enginecore.model.graph_reference import GraphReference


class HardwareDataSource:
    graph_ref = GraphReference()

    @classmethod
    def get_all_assets(cls):
        return NotImplementedError()

    @classmethod
    def get_affected_assets(cls, asset_key):
        return NotImplementedError()

    @classmethod
    def get_mains_powered_assets(cls):
        return NotImplementedError()


class HardwareGraphDataSource(HardwareDataSource):

    graph_ref = None

    @classmethod
    def init_connection(cls):
        cls.graph_ref = GraphReference()

    @classmethod
    def get_all_assets(cls):
        with cls.graph_ref.get_session() as session:
            return GraphReference.get_assets_and_children(session)

    @classmethod
    @functools.lru_cache(maxsize=200)
    def get_affected_assets(cls, asset_key):
        with cls.graph_ref.get_session() as session:
            childen, parents, _ = GraphReference.get_affected_assets(session, asset_key)

        return ([a["key"] for a in childen], [a["key"] for a in parents])

    @classmethod
    @functools.lru_cache(maxsize=200)
    def get_mains_powered_assets(cls):
        with cls.graph_ref.get_session() as session:
            return GraphReference.get_mains_powered_outlets(session)

    @classmethod
    @functools.lru_cache(maxsize=200)
    def get_parent_assets(cls, asset_key):
        """Get parent asset keys (nodes that are powering the asset)
        Args:
            asset_key(int): child key
        Returns:
            list: parent asset keys
        """

        with cls.graph_ref.get_session() as session:
            parent_assets = GraphReference.get_parent_assets(session, asset_key)

        return [a["key"] for a in parent_assets]

    @classmethod
    @functools.lru_cache(maxsize=200)
    def get_asset_oid_info(cls, asset_key, oid):
        """Get oid information based on provided asset key and object id"""
        with cls.graph_ref.get_session() as session:
            return GraphReference.get_asset_oid_info(session, asset_key, oid)

    @classmethod
    def cache_clear_all(cls):
        """clear all cached data"""
        cls.get_affected_assets.cache_clear()
        cls.get_mains_powered_assets.cache_clear()
        cls.get_parent_assets.cache_clear()
        cls.get_asset_oid_info.cache_clear()

    @classmethod
    def close(cls):
        """Close down driver"""
        cls.graph_ref.close()
