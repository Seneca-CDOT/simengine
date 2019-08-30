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

    @dual-psu-asset
    @server-power-toggle
    Scenario Outline: Toggling server power should affect PSU load
        Given Outlet asset with key "2" is created
        And Server asset with key "7", "2" PSU(s) and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running
        And asset "7" is "<server-ini>"

        When asset "7" goes "<server-new>"

        # check load for assets
        Then asset "1" load is set to "<1>"
        Then asset "2" load is set to "<2>"

        And asset "71" load is set to "<71>"
        And asset "72" load is set to "<72>"

        And asset "7" load is set to "<7>"
        Examples: Toggling server status results in load update
            | server-ini | server-new | 1   | 2   | 71  | 72  | 7   |
            | online     | online     | 2.0 | 2.0 | 2.0 | 2.0 | 4.0 |
            | online     | offline    | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
            | offline    | online     | 2.0 | 2.0 | 2.0 | 2.0 | 4.0 |

    @dual-psu-asset
    @server-bmc-asset
    @server-power-toggle
    Scenario Outline: Toggling server bmc power should affect PSU load
        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running
        And asset "7" is "<server-ini>"

        When asset "7" goes "<server-new>"

        # check load for assets
        Then asset "1" load is set to "<1>"
        Then asset "2" load is set to "<2>"

        And asset "71" load is set to "<71>"
        And asset "72" load is set to "<72>"

        And asset "7" load is set to "<7>"
        Examples: Toggling server status results in load update
            | server-ini | server-new | 1    | 2    | 71   | 72   | 7   |
            | online     | online     | 2.25 | 2.25 | 2.25 | 2.25 | 4.0 |
            | online     | offline    | 0.25 | 0.25 | 0.25 | 0.25 | 0.0 |
            | offline    | online     | 2.25 | 2.25 | 2.25 | 2.25 | 4.0 |

    @dual-psu-asset
    @server-bmc-asset
    @server-power-toggle
    @corner-case
    Scenario Outline: Special Server case with PSU power change and then server state toggling

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running
        And asset "7" is "<server-ini>"

        When asset "<psu-key>" goes "<psu-ini>"
        And asset "7" goes "<server-new>"

        # check load for assets
        Then asset "1" load is set to "<1>"
        And asset "2" load is set to "<2>"

        And asset "71" load is set to "<71>"
        And asset "72" load is set to "<72>"

        And asset "7" load is set to "<7>"
        Examples: Toggling server and psu status results in load update
            | psu-key | psu-ini | server-ini | server-new | 1    | 2    | 71   | 72   | 7   |
            | 71      | offline | online     | offline    | 0.00 | 0.25 | 0.0  | 0.25 | 0.0 |
            | 72      | offline | online     | offline    | 0.25 | 0.00 | 0.25 | 0.0  | 0.0 |
            | 72      | offline | offline    | online     | 4.25 | 0.00 | 4.25 | 0.0  | 4.0 |


    @dual-psu-asset
    @server-bmc-asset
    @server-power-toggle
    @corner-case
    Scenario Outline: Special Server case with server going offline and then PSU power change

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running
        And asset "7" is "<server-ini>"

        When asset "7" goes "<server-new>"
        And asset "<psu-key>" goes "<psu-ini>"
        And asset "<psu-key>" goes "<psu-new>"

        # check load for assets
        Then asset "1" load is set to "<1>"
        And asset "2" load is set to "<2>"

        And asset "71" load is set to "<71>"
        And asset "72" load is set to "<72>"

        And asset "7" load is set to "<7>"
        Examples: Toggling server and psu status results in load update
            | server-ini | server-new | psu-key | psu-ini | psu-new | 1    | 2    | 71   | 72   | 7   |
            | online     | offline    | 71      | offline | online  | 2.25 | 2.25 | 2.25 | 2.25 | 4.0 |
            | online     | offline    | 72      | offline | online  | 2.25 | 2.25 | 2.25 | 2.25 | 4.0 |


    @corner-case
    @dual-psu-asset
    @server-bmc-asset
    Scenario Outline: Load of an offline server remains unchanged when it is set not to power when AC restored

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created
        And asset "7" "does not power on" when AC is restored

        And asset "1" powers target "71"
        And asset "2" powers target "72"

        And Engine is up and running
        And asset "7" is "offline"
        And asset "<key-1>" is "<1-ini>"
        And asset "<key-2>" is "<2-ini>"

        # Test conditions, when this happens:
        When asset "<key-1>" goes "<1-new>"
        And asset "<key-2>" goes "<2-new>"

        # Then the load outcome/result is:
        Then asset "1" load is set to "<1>"
        And asset "2" load is set to "<2>"

        And asset "71" load is set to "<71>"
        And asset "72" load is set to "<72>"
        And asset "7" load is set to "<7>"


        Examples: Check that AC state update does not affect load of the server asset (toggling outlets)
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   | 1    | 2    | 71   | 72   | 7   |
            | 1     | 2     | offline | offline | online  | online  | 0.25 | 0.25 | 0.25 | 0.25 | 0.0 |
            | 1     | 2     | offline | offline | offline | online  | 0.00 | 0.25 | 0.00 | 0.25 | 0.0 |
            | 1     | 2     | offline | offline | online  | offline | 0.25 | 0.00 | 0.25 | 0.00 | 0.0 |

        Examples: Check that AC state update does not affect load of the server asset (toggling PSUs)
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   | 1    | 2    | 71   | 72   | 7   |
            | 71    | 72    | offline | offline | online  | online  | 0.25 | 0.25 | 0.25 | 0.25 | 0.0 |
            | 71    | 72    | offline | offline | offline | online  | 0.00 | 0.25 | 0.00 | 0.25 | 0.0 |
            | 71    | 72    | offline | offline | online  | offline | 0.25 | 0.00 | 0.25 | 0.00 | 0.0 |

    @corner-case
    @dual-psu-asset
    @server-bmc-asset
    Scenario: Load re-distribution works with option power-on-AC-restored set to off
        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created
        And asset "7" "does not power on" when AC is restored

        And asset "1" powers target "71"
        And asset "2" powers target "72"

        And Engine is up and running

        When asset "71" goes "offline"
        And asset "71" goes "online"

        Then asset "1" load is set to "2.25"
        And asset "2" load is set to "2.25"

        And asset "71" load is set to "2.25"
        And asset "72" load is set to "2.25"

        And asset "7" load is set to "4.0"

    @dual-psu-asset
    Scenario Outline: Dual-PSU load re-distribution
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
        Examples: Switching states from online to offline for outlets powering 2 PSUs should affect load
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new   | 2-new   | 1   | 2   | 1801 | 1802 | 180 |
            | 1     | 2     | online | online | online  | online  | 2.0 | 2.0 | 2.0  | 2.0  | 4.0 |
            | 1     | 2     | online | online | online  | offline | 4.0 | 0.0 | 4.0  | 0.0  | 4.0 |
            | 1     | 2     | online | online | offline | online  | 0.0 | 4.0 | 0.0  | 4.0  | 4.0 |
            | 1     | 2     | online | online | offline | offline | 0.0 | 0.0 | 0.0  | 0.0  | 0.0 |

        Examples: Switching states from online to offline for 2 PSUs should affect load
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new   | 2-new   | 1   | 2   | 1801 | 1802 | 180 |
            | 1801  | 1802  | online | online | online  | online  | 2.0 | 2.0 | 2.0  | 2.0  | 4.0 |
            | 1801  | 1802  | online | online | online  | offline | 4.0 | 0.0 | 4.0  | 0.0  | 4.0 |
            | 1801  | 1802  | online | online | offline | online  | 0.0 | 4.0 | 0.0  | 4.0  | 4.0 |
            | 1801  | 1802  | online | online | offline | offline | 0.0 | 0.0 | 0.0  | 0.0  | 0.0 |

        Examples: Switching states from offline to online for outlets powering PSUs should affect load
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   | 1   | 2   | 1801 | 1802 | 180 |
            | 1     | 2     | offline | offline | online  | online  | 2.0 | 2.0 | 2.0  | 2.0  | 4.0 |
            | 1     | 2     | offline | offline | online  | offline | 4.0 | 0.0 | 4.0  | 0.0  | 4.0 |
            | 1     | 2     | offline | offline | offline | online  | 0.0 | 4.0 | 0.0  | 4.0  | 4.0 |
            | 1     | 2     | offline | offline | offline | offline | 0.0 | 0.0 | 0.0  | 0.0  | 0.0 |



    @dual-psu-asset
    Scenario Outline: Dual-PSU load changes with wallpower voltage
        # initialize model & engine
        # (1)-[powers]->[1801:   server ]
        # (2)-[powers]->[1802     180   ]
        Given Outlet asset with key "2" is created
        And Server asset with key "180", "2" PSU(s) and "480" Wattage is created

        And asset "1" powers target "1801"
        And asset "2" powers target "1802"
        And Engine is up and running

        When wallpower voltage is updated to "<new-volt>"

        # check load for assets
        Then asset "1" load is set to "<1>"
        Then asset "2" load is set to "<2>"

        And asset "1801" load is set to "<1801>"
        And asset "1802" load is set to "<1802>"

        And asset "180" load is set to "<180>"

        Examples: Downstream voltage drop chaining
            | new-volt | 1   | 2   | 1801 | 1802 | 180 |
            | 0        | 0.0 | 0.0 | 0.0  | 0.0  | 0.0 |
            | 240      | 1.0 | 1.0 | 1.0  | 1.0  | 2.0 |
            | 60       | 4.0 | 4.0 | 4.0  | 4.0  | 8.0 |


    @dual-psu-asset
    @server-bmc-asset
    Scenario Outline: Load is distributed with ServerBMC with PSUs drawing power
        Given Outlet asset with key "2" is created
        And Outlet asset with key "22" is created

        And ServerBMC asset with key "9" and "480" Wattage is created

        And asset "1" powers target "91"
        And asset "2" powers target "22"
        And asset "22" powers target "92"

        And Engine is up and running
        # Set up initial state
        And asset "<key-1>" is "<1-ini>"
        And asset "<key-2>" is "<2-ini>"

        # Test conditions:
        When asset "<key-1>" goes "<1-new>"
        And asset "<key-2>" goes "<2-new>"

        # check load for assets
        Then asset "1" load is set to "<1>"
        Then asset "2" load is set to "<2>"
        Then asset "22" load is set to "<22>"

        And asset "91" load is set to "<91>"
        And asset "92" load is set to "<92>"

        And asset "9" load is set to "<9>"

        Examples: All Power Sources present
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new  | 2-new  | 1    | 2    | 22   | 91   | 92   | 9   |
            | 1     | 2     | online | online | online | online | 2.25 | 2.25 | 2.25 | 2.25 | 2.25 | 4.0 |


        Examples: Having both power sources offline should result in zero load
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new   | 2-new   | 1    | 2    | 22   | 91   | 92   | 9    |
            | 1     | 2     | online | online | offline | offline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
            | 1     | 22    | online | online | offline | offline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
            | 91    | 92    | online | online | offline | offline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
            | 91    | 92    | online | online | offline | offline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |


        # manipulate 2 input power streams for the server
        # (each powering a PSU)
        Examples: Switching states from online to offline for outlets powering 2 PSUs should affect load
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new   | 2-new   | 1    | 2    | 22   | 91   | 92   | 9   |
            | 1     | 2     | online | online | online  | online  | 2.25 | 2.25 | 2.25 | 2.25 | 2.25 | 4.0 |
            | 1     | 2     | online | online | offline | online  | 0.00 | 4.25 | 4.25 | 0.0  | 4.25 | 4.0 |
            | 1     | 2     | online | online | online  | offline | 4.25 | 0.00 | 0.00 | 4.25 | 0.00 | 4.0 |
            | 1     | 22    | online | online | online  | offline | 4.25 | 0.00 | 0.00 | 4.25 | 0.00 | 4.0 |

        Examples: Switching states from online to offline for PSUs should affect load
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new   | 2-new   | 1    | 2    | 22   | 91   | 92   | 9   |
            | 91    | 92    | online | online | offline | online  | 0.00 | 4.25 | 4.25 | 0.0  | 4.25 | 4.0 |
            | 91    | 92    | online | online | online  | offline | 4.25 | 0.00 | 0.00 | 4.25 | 0.00 | 4.0 |
            | 91    | 92    | online | online | online  | offline | 4.25 | 0.00 | 0.00 | 4.25 | 0.00 | 4.0 |

        Examples: Switching states from offline to online for outlets powering 2 PSUs should affect load
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   | 1    | 2    | 22   | 91   | 92   | 9   |
            | 1     | 2     | offline | offline | online  | online  | 2.25 | 2.25 | 2.25 | 2.25 | 2.25 | 4.0 |
            | 1     | 2     | offline | offline | offline | online  | 0.00 | 4.25 | 4.25 | 0.0  | 4.25 | 4.0 |
            | 1     | 2     | offline | offline | online  | offline | 4.25 | 0.00 | 0.00 | 4.25 | 0.00 | 4.0 |

        Examples: Switching states from offline to online for PSUs should affect load
            | key-1 | key-2 | 1-ini   | 2-ini   | 1-new   | 2-new   | 1    | 2    | 22   | 91   | 92   | 9   |
            | 91    | 92    | offline | offline | online  | online  | 2.25 | 2.25 | 2.25 | 2.25 | 2.25 | 4.0 |
            | 91    | 92    | offline | offline | offline | online  | 0.00 | 4.25 | 4.25 | 0.0  | 4.25 | 4.0 |
            | 91    | 92    | offline | offline | online  | offline | 4.25 | 0.00 | 0.00 | 4.25 | 0.00 | 4.0 |

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

    @slow
    @server-bmc-asset
    @ipmi-interface
    @unreliable
    Scenario Outline: PSU load sensors get updated with PSU load

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running
        And asset "<key-1>" is "<1-ini>"
        And asset "<key-2>" is "<2-ini>"

        # Test conditions:
        When asset "<key-1>" goes "<1-new>"
        And asset "<key-2>" goes "<2-new>"

        # ipmi_sim reads from a file with a delay
        And pause for "2" seconds

        Then asset "7" BMC sensor "<sensor-name>" value is "<sensor-value>"

        Examples: All power sources are present
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new  | 2-new  | sensor-name  | sensor-value |
            | 1     | 2     | online | online | online | online | PSU1 current | 2 Amps       |
            | 1     | 2     | online | online | online | online | PSU2 current | 2 Amps       |

        Examples: One source is off
            | key-1 | key-2 | 1-ini  | 2-ini  | 1-new  | 2-new   | sensor-name  | sensor-value |
            | 1     | 2     | online | online | online | offline | PSU1 current | 4 Amps       |
            | 1     | 2     | online | online | online | offline | PSU2 current | 0 Amps       |

        Examples: One source was off but went back online
            | key-1 | key-2 | 1-ini  | 2-ini   | 1-new  | 2-new  | sensor-name  | sensor-value |
            | 1     | 2     | online | offline | online | online | PSU1 current | 2 Amps       |
            | 1     | 2     | online | offline | online | online | PSU2 current | 2 Amps       |

    @slow
    @server-bmc-asset
    @ipmi-interface
    @unreliable
    Scenario Outline: PSU load sensors get updated when server status changes

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running

        And asset "7" is "<server-ini>"
        When asset "7" goes "<server-new>"

        # ipmi_sim reads from a file with a delay
        And pause for "2" seconds

        Then asset "7" BMC sensor "<sensor-name-1>" value is "<sensor-value-1>"
        Then asset "7" BMC sensor "<sensor-name-2>" value is "<sensor-value-2>"

        Examples: BMC amperage sensors change with server status
            | server-ini | server-new | sensor-name-1 | sensor-value-1 | sensor-name-2 | sensor-value-2 |
            | offline    | online     | PSU1 current  | 2 Amps         | PSU2 current  | 2 Amps         |
            | online     | offline    | PSU1 current  | 0 Amps         | PSU2 current  | 0 Amps         |
