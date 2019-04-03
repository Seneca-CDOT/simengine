"""Contains tools for simplifying query building process """
import secrets
import string
import random
import re


def get_props_stm(attr: dict, supported_attr: list = None) -> str:
    """Format dict attributes as neo4j props
    e.g. CREATE (node:Label {attr1: attrValue1, attr2: attrValue2})
    Args:
        attr: node properties mapped to prop values
        supported_attr: valid node properties, used for filtering out attributes
    Returns:
        str: statement formatted for neo4j query
    """

    existing = dict(
        filter(
            lambda k: attr[k[0]] is not None
            and (not supported_attr or k[0] in supported_attr),
            attr.items(),
        )
    )
    return ",".join(
        map(lambda k: "{}: {}".format(to_camelcase(k), repr(existing[k])), existing)
    )


def get_set_stm(
    attr: dict, node_name: str = "asset", supported_attr: list = None
) -> str:
    """Format dict as neo4j set statement ( nodeName.nodeProp=nodeValue )
    e.g. MATCH (node) SET node.attr1=attrValue1
    Args:
        attr: node properties mapped to new values
        node_name: name given to a graph node (node to be updated)
        supported_attr: valid node properties, used for filtering out attributes
    Returns:
        str: set statement formatted for neo4j query 
    """

    existing = dict(
        filter(
            lambda k: attr[k[0]] is not None
            and (not supported_attr or k[0] in supported_attr),
            attr.items(),
        )
    )
    return ",".join(
        map(
            lambda k: "{}.{}={}".format(node_name, to_camelcase(k), repr(existing[k])),
            existing,
        )
    )


def get_oid_desc_stm(oid_desc):
    """Format oid descriptions (int->value mappings) for neo4j """
    return ",".join(map(lambda k: '`{}`: "{}"'.format(oid_desc[k], k), oid_desc))


def to_camelcase(snake_string):
    """Convert snakecase to camelcase """
    return re.sub(r"(?!^)_([a-zA-Z])", lambda m: m.group(1).upper(), snake_string)


def generate_id(size=12, chars=string.ascii_uppercase + string.digits):
    """Ref: https://stackoverflow.com/a/23728630"""
    return "".join(secrets.choice(chars) for _ in range(size))


def generate_mac():
    """Generate a MAC address """
    return "".join(random.choice("0123456789abcdef") for _ in range(12))
