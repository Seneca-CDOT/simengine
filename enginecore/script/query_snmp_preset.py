#!/usr/bin/python3

""" A helper script to retrieve OIDs defined in model presets (oids that are
manipulated by SimEngine);
This can be used to debug snmp interface;

Usage:
  ./script/query_snmp_preset.py -f ./enginecore/model/presets/apc_ups.json -H 10.20.3.1
"""

import argparse

import json
import subprocess
import sys


def query_snmp_interface(oid, host="localhost", port=1024):
    """Helper function to query snmp interface of a device"""
    out = subprocess.check_output(
        "snmpget -c private -v1 {host}:{port} {oid}".format(
            host=host, port=port, oid=oid
        ),
        shell=True,
    ).decode("utf-8")
    return out


if __name__ == "__main__":

    # parse cli option
    argparser = argparse.ArgumentParser(description="Query all OIDs in a preset file")

    argparser.add_argument("-H", "--host", help="Snmp Host", type=str, required=True)
    argparser.add_argument("-p", "--port", help="Snmp port", type=int, default=161)
    argparser.add_argument(
        "-f", "--file-preset", help=".JSON preset file", type=str, required=True
    )

    args = vars(argparser.parse_args())

    with open(args["file_preset"]) as preset_handler:
        data = json.load(preset_handler)

    if not "OIDs" in data:
        print("No oids in the preset file!", file=sys.stderr)
        exit(1)

    for oid_name in data["OIDs"]:
        oid = data["OIDs"][oid_name]["OID"]
        oid_value = query_snmp_interface(oid, host=args["host"], port=args["port"])
        print(oid_name + ":" + oid)
        print(" > " + oid_value)
