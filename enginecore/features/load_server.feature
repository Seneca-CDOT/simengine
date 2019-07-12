@not-ci-friendly
@server-asset
@load-behaviour
@power-behaviour
Feature: Server Load Handling
    Server may handle load differently depending on how many power sources it has;
    Servers with dual psu have 2 power sources meaning load gets re-distributed to the
    alternative power source/parent if one PSU goes offline;

    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created

    Scenario Outline: Dual-PSU load re-destribution
        # initialize model & engine
        # (1)-[powers]->[1801:   server ]
        # (2)-[powers]->[1802     180   ]
        Given Outlet asset with key "2" is created
        And Server asset with key "180", "2" PSU(s) and "480" Wattage is created

        And asset "1" powers target "1801"
        And asset "2" powers target "1802"
        And Engine is up and running

        # Set up initial state
        And asset "<key-1>" is "<1-ini>"
        And asset "<key-2>" is "<2-ini>"

        # Test conditions, when this happens:
        When asset "<key-1>" goes "<1-new>"
        And asset "<key-2>" goes "<2-new>"

        # check load for assets
        Then asset "1" load is set to "<1>"
        Then asset "2" load is set to "<2>"

        And asset "1801" load is set to "<1801>"
        And asset "1802" load is set to "<1802>"

        And asset "180" load is set to "<180>"

        # manipulate 2 input power streams for the server
        # (each powering a PSU)
        Examples: Switching states from online to offline for dual power supply should affect load
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new  | 2-new  | 1   | 2   | 1801 | 1802 | 180 |
            | 1     | 2     | online | online | online | online | 2.0 | 2.0 | 2.0  | 2.0  | 4.0 |


    Scenario Outline: Single PSU server acts just like a regular asset
        # initialize model & engine
        # (1)-[powers]->[1801:   server 180]
        Given Server asset with key "180", "1" PSU(s) and "120" Wattage is created
        And asset "1" powers target "1801"
        And Engine is up and running
        And asset "<key>" is "<state-ini>"

        When asset "<key>" goes "<state-new>"

        # check load for assets
        Then asset "1" load is set to "<1>"
        And asset "1801" load is set to "<1801>"
        And asset "180" load is set to "<180>"


        Examples: Single-psu server state going offline
            | key  | state-ini | state-new | 1   | 1801 | 180 |
            | 1    | online    | offline   | 0.0 | 0.0  | 0.0 |
            | 1801 | online    | offline   | 0.0 | 0.0  | 0.0 |
            | 180  | online    | offline   | 0.0 | 0.0  | 0.0 |

        Examples: Single-psu server state going online
            | key  | state-ini | state-new | 1   | 1801 | 180 |
            | 1    | online    | online    | 1.0 | 1.0  | 1.0 |
            | 1    | offline   | online    | 1.0 | 1.0  | 1.0 |
            | 1801 | offline   | online    | 1.0 | 1.0  | 1.0 |
            | 180  | offline   | online    | 1.0 | 1.0  | 1.0 |
