
# not ci friendly because this requires a VM running (with vm name set in behave.ini)
@not-ci-friendly
@server-asset
@voltage-behaviour
@power-behaviour
Feature: Power logic for Server asset type
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
        And asset "180" vm is "<180>"

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
        And asset "180" vm is "<180>"

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


    @dual-psu-asset
    @server-bmc-asset
    @server-power-toggle
    @corner-case
    Scenario: More complicated case with server and psu power update

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"

        And Engine is up and running

        And asset "71" is "offline"
        And asset "7" is "offline"
        And asset "72" is "offline"

        When asset "71" goes "online"

        Then asset "7" is "online"
        And asset "7" vm is "online"
        And asset "71" is "online"

    @corner-case
    @dual-psu-asset
    @server-bmc-asset
    Scenario Outline: State of an offline server remains unchanged when it is set not to power when AC restored

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created
        And asset "7" "does not power on" when AC is restored

        And asset "1" powers target "71"
        And asset "2" powers target "72"

        And Engine is up and running
        And asset "7" is "offline"

        # Test conditions, when this happens:
        When asset "<key-1>" goes "<1-new>"
        And asset "<key-2>" goes "<2-new>"

        # Then the result is:
        Then asset "7" is "offline"
        And asset "7" vm is "offline"

        Examples: Check that AC state update does not affect power state of the server asset
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   |
            | 1     | 2     | offline | offline | online  | online  |
            | 1     | 2     | offline | offline | offline | online  |
            | 1     | 2     | offline | offline | online  | offline |

    @ipmi-interface
    @server-bmc-asset
    @slow
    @unreliable
    Scenario Outline: IPMI agent is not available when all power supplies are off

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running

        And asset "<key-1>" is "<1-ini>"
        And asset "<key-2>" is "<2-ini>"

        When asset "<key-2>" goes "<1-new>"
        And asset "<key-1>" goes "<2-new>"
        And pause for "2" seconds

        Then asset "7" ipmi interface is "<ipmi-status>"

        Examples: Outlets - Check that IPMI agent goes offline when all power supplies are off
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   | ipmi-status |
            | 1     | 2     | offline | offline | online  | online  | reachable   |
            | 1     | 2     | offline | offline | offline | online  | reachable   |
            | 1     | 2     | offline | offline | online  | offline | reachable   |
            | 1     | 2     | offline | offline | offline | offline | unreachable |
            | 1     | 2     | online  | online  | offline | offline | unreachable |

        Examples: PSUs - Check that IPMI agent goes offline when all power supplies are off
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   | ipmi-status |
            | 71    | 72    | offline | offline | online  | offline | reachable   |
            | 71    | 72    | offline | offline | offline | offline | unreachable |

    @ipmi-interface
    @server-bmc-asset
    @slow
    @unreliable
    Scenario Outline: IPMI board chassis status changes with server status

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running

        When asset "7" goes "<server-status>"
        And pause for "2" seconds

        Then asset "7" ipmi chassis status is "<chassis-status>"

        Examples: Toggling server status results in chassis power change
            | server-status | chassis-status |
            | online        | online         |
            | offline       | offline        |

    @slow
    @wip
    @server-bmc-asset
    @ipmi-interface
    @unreliable
    Scenario Outline: BMC Sensors are set to their offline states when server is offline
            """
            For example, case fans would stop spinning
            """
        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running

        And asset "7" is "<1-ini>"
        When asset "7" goes "<1-new>"

        # ipmi_sim reads from a file with a delay
        And pause for "2" seconds

        Then asset "7" BMC sensor "PSU1 Fan" value is "<sensor-value>"

        Examples: AC changes to a PSU affect PSU fan status
            | 1-ini   | 1-new   | sensor-value |
            | online  | offline | 0 RPM        |
            | offline | online  | 1000 RPM     |

    @slow
    @server-bmc-asset
    @ipmi-interface
    @unreliable
    Scenario Outline: PSU fans go offline with power loss to a PSU they are cooling
            """
            PSU fans go offline with AC (this is outlined in "Power Tests" section
            on Anvil https://www.alteeve.com/w/Build_an_m2_Anvil!)
            """

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running

        And asset "1" is "<1-ini>"
        When asset "1" goes "<1-new>"

        # ipmi_sim reads from a file with a delay
        And pause for "2" seconds

        Then asset "7" BMC sensor "<sensor-name>" value is "<sensor-value>"

        Examples: AC changes to a PSU affect PSU fan status
            | 1-ini   | 1-new   | sensor-name | sensor-value |
            | online  | online  | PSU1 Fan    | 1000 RPM     |
            | online  | offline | PSU1 Fan    | 0 RPM        |
            | offline | online  | PSU1 Fan    | 1000 RPM     |
