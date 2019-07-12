@not-ci-friendly
@server-asset
@voltage-behaviour
@power-behaviour
Feature: Dual PSU Voltage Handling
    Servers with dual psu have 2 power sources meaning that if
    one source fails, another one takes over.

    Background:
        Given the system model is empty
        # initialize model & engine
        # (1)-[powers]->[1801:   server ]
        # (2)-[powers]->[1802     180   ]
        And Outlet asset with key "1" is created
        And Outlet asset with key "2" is created
        And Server asset with key "180", "2" PSU(s) and "480" Wattage is created

        And asset "1" powers target "1801"
        And asset "2" powers target "1802"
        And Engine is up and running

    Scenario Outline: Server powered by 2 PSU's requires at least one power source present

        # Set up initial state
        Given asset "<key-1>" is "<1-ini>"
        And asset "<key-2>" is "<2-ini>"

        # Test conditions, when this happens:
        When asset "<key-1>" goes "<1-new>"
        And asset "<key-2>" goes "<2-new>"

        # Then the result is:

        Then asset "1801" is "<1801>"
        And asset "1802" is "<1802>"
        And asset "180" is "<180>"

        Examples: Switching states for dual power supply for server
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new   | 2-new   | 1801    | 1802    | 180    |
            | 1     | 2     | online | online | online  | online  | online  | online  | online |
            | 1     | 2     | online | online | online  | offline | online  | offline | online |
            | 1     | 2     | online | online | offline | online  | offline | online  | online |

