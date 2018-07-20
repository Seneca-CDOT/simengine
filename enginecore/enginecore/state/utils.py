""" Various helper functions """
from enginecore.state.asset_definition import SUPPORTED_ASSETS


def format_as_redis_key(key, oid, key_formatted=True):
    """Convert asset key & OID into SNMPSim format as 
        `{asset-key}-{oid}` where each OID digits are padded with 9 zeros
    Args:
        key(str): asset key
        oid(str): unformatted OID e.g. 1.3.6.1.4.1.13742.4.1.2.2.1.3.3
    Returns:
        str: Redis key for the asset key-oid pair e
    """
    if not key_formatted:
        key = key.zfill(10)

    key_and_oid = key + '-'
    oid_digits = oid.split('.')

    for digit in oid_digits[:-1]:
        key_and_oid += (digit + '.').rjust(11, ' ')
    key_and_oid += (oid_digits[-1]).rjust(10, ' ')

    return key_and_oid
    

def get_asset_type(labels):
    """Find if any of the labels indicate asset type 
    
    Args:
        labels(list): labels that are assigned to a particular node
    
    Returns:
        string: supported asset label formatted for the state store
    
    Raises:
        StopIteration: when asset type is either not supported or undefined in the graph ref
    """

    asset_label = set(SUPPORTED_ASSETS).intersection(
        map(lambda x: x.lower(), labels)
    )

    return next(iter(asset_label)).lower()
    
