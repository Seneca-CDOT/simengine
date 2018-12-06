'''Contains tools for simplifying query building process '''
import secrets
import string
import random
import re

def get_props_stm(attr, supported_attr=None):
    """Format dict attributes as neo4j props ( attr: attrValue )"""

    existing = dict(
        filter(lambda k: attr[k[0]] is not None and (not supported_attr or k[0] in supported_attr), attr.items())
    )
    return ','.join(map(lambda k: "{}: {}".format(to_camelcase(k), repr(existing[k])), existing))


def get_set_stm(attr, node_name="asset", supported_attr=None):
    """Format dict as neo4j set statement ( nodeName.nodeProp=nodeValue ) """

    existing = dict(
        filter(lambda k: attr[k[0]] is not None and (not supported_attr or k[0] in supported_attr), attr.items())
    )
    return ','.join(map(lambda k: "{}.{}={}".format(node_name, to_camelcase(k), repr(existing[k])), existing))


def get_oid_desc_stm(oid_desc):
    """Format oid descriptions (int->value mappings) for neo4j """
    return ','.join(map(lambda k: '{}: "{}"'.format(oid_desc[k], k), oid_desc))


def to_camelcase(snake_string):
    """Convert snakecase to camelcase """    
    return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), snake_string)


def generate_id(size=12, chars=string.ascii_uppercase + string.digits):
    """Ref: https://stackoverflow.com/a/23728630"""
    return ''.join(secrets.choice(chars) for _ in range(size))


def generate_mac():
    """Generate a MAC address """
    return ''.join(random.choice('0123456789abcdef') for _ in range(12))
