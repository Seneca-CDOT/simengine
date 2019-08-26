@not-ci-friendly
@server-asset
@voltage-behaviour
@power-behaviour
Feature: Server Voltage Handling
    Server may handle voltage differently depending on how many power sources it has;
    Servers with dual psu have 2 power sources meaning that if
    one source fails, another one takes over.

    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created

    Scenario Outline: Single PSU server acts just like a regular asset
        # initialize model & engine
        # (1)-[powers]->[1801:   server 180]
        Given Server asset with key "180", "1" PSU(s) and "120" Wattage is created
        And asset "1" powers target "1801"
        And Engine is up and running

        When asset "1" goes "<status>"

        Then asset "1801" is "<1801>"
        And asset "180" is "<180>"

        Examples: Single-psu server state tests
            | key  | status  | 1801    | 180     |
            | 1    | offline | offline | offline |
            | 1801 | offline | offline | offline |

    @dual-psu-asset
    Scenario Outline: Server powered by 2 PSU's requires at least one power source present

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

        # Then the result is:

        Then asset "1801" is "<1801>"
        And asset "1802" is "<1802>"
        And asset "180" is "<180>"

        Examples: Switching states from online to offline for dual power supply
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new   | 2-new   | 1801    | 1802    | 180     |
            | 1     | 2     | online | online | online  | online  | online  | online  | online  |
            | 1     | 2     | online | online | online  | offline | online  | offline | online  |
            | 1     | 2     | online | online | offline | offline | offline | offline | offline |

        Examples: Switching states from offline to online for dual power supply
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   | 1801    | 1802    | 180    |
            | 1     | 2     | offline | online  | online  | online  | online  | online  | online |
            | 1     | 2     | offline | offline | offline | online  | offline | online  | online |
            | 1     | 2     | offline | offline | online  | offline | online  | offline | online |
