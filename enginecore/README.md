## Setting Up

### Install and configure

Run the installation script:
'script/simengine-setup'

This will run the series of scripts in script/setup/

Note that some components are not yet packaged as RPMs,
and these components are installed from other sources
(e.g., pip). Note also that additional repositories may
be added to the system's yum/dnf configuration by this
script.

## Run

Run the script:
'script/simengine-run'

## Linting

`sudo python3 -m pip install pylint`

This lintrc file is based on Google Style Guide. See this docstring [example](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for documentation format reference.


## Sample Unit test invocation

Server tests:

`python3 -m unittest tests.server_load_m1`

PDU Snmp tests:

`python3 -m unittest tests.snmp_pdu`

UPS Snmp tests:

`python3 -m unittest tests.snmp_ups`