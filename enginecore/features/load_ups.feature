@ups-asset
@load-behaviour
@power-behaviour
Feature: UPS Load Handling
    UPS is a special kind of asset that can stop load propagation upstream if
    it is running on battery and there's no input power. Load also affects
    UPS remaining runtime.

    Background:
        Given the system model is empty
        And UPS asset with key "190" and "1024" port is created

    Scenario Outline: Load changes across topology

        # scenario-specific model
        Given Outlet asset with key "1" is created
        And Lamp asset with key "3", minimum "109" Voltage and "240" Wattage is created

        # connect together
        And asset "1" powers target "190"
        And asset "1903" powers target "3"

        And Engine is up and running
        And asset "<asset-key>" is "<asset-ini-state>"

        # create a certain power condition
        When asset "<asset-key>" goes "<asset-new-state>"

        # == check states ==
        Then asset "1" load is set to "<1>"
        Then asset "190" load is set to "<190>"
        Then asset "1903" load is set to "<1903>"
        Then asset "3" load is set to "<3>"


        Examples: Check load with online as initial state
            | asset-key | asset-ini-state | asset-new-state | 1   | 190 | 1903 | 3   |
            | 1         | online          | online          | 2.2 | 2.2 | 2.0  | 2.0 |
            | 1         | online          | offline         | 0.0 | 2.2 | 2.0  | 2.0 |
            | 190       | online          | offline         | 0.0 | 0.0 | 0.0  | 0.0 |

        Examples: Check load with offline as initial state
            | asset-key | asset-ini-state | asset-new-state | 1   | 190 | 1903 | 3   |
            | 1         | offline         | online          | 2.2 | 2.2 | 2.0  | 2.0 |
            | 190       | offline         | online          | 2.2 | 2.2 | 2.0  | 2.0 |

    Scenario Outline: Load propagation is blocked in upstream direction when UPS power source is down

        # create this topology:
        # (1)->(7:71)->(190:193)->(3)
        #      (  74)->(4)
        Given Outlet asset with key "1" is created
        And PDU asset with key "7",  minimum "105" Voltage and "1025" port is created
        And Lamp asset with key "3", minimum "109" Voltage and "240" Wattage is created
        And Lamp asset with key "4", minimum "109" Voltage and "120" Wattage is created

        And asset "1" powers target "7"
        And asset "71" powers target "190"
        And asset "74" powers target "4"
        And asset "1903" powers target "3"

        And Engine is up and running

        # state pre-conditions
        And asset "1" is "<out-state>"
        And asset "<asset-key>" is "<asset-ini-state>"

        # create a certain power condition
        When asset "<asset-key>" goes "<asset-new-state>"

        # == check states ==
        Then asset "1" load is set to "<1>"
        Then asset "7" load is set to "<7>"
        Then asset "71" load is set to "<71>"

        Then asset "190" load is set to "<190>"

        # ups output outlets
        Then asset "1903" load is set to "<1903>"
        # lamps (leaf nodes)
        Then asset "3" load is set to "<3>"
        Then asset "4" load is set to "<4>"

        Examples: Top-parent power source checks
            | out-state | asset-key | asset-ini-state | asset-new-state | 1   | 7   | 71  | 190 | 1903 | 3   | 4   |
            | online    | 1905      | online          | offline         | 3.2 | 3.2 | 2.2 | 2.2 | 2.0  | 2.0 | 1.0 |
            | offline   | 1905      | online          | offline         | 0.0 | 0.0 | 0.0 | 2.2 | 2.0  | 2.0 | 0.0 |
            | online    | 3         | online          | offline         | 1.2 | 1.2 | 0.2 | 0.2 | 0.0  | 0.0 | 1.0 |


        Examples: Leaf-node lamp power changes with absent top-parent power source
            | out-state | asset-key | asset-ini-state | asset-new-state | 1   | 7   | 71  | 190 | 1903 | 3   | 4   |
            | offline   | 3         | online          | offline         | 0.0 | 0.0 | 0.0 | 0.2 | 0.0  | 0.0 | 0.0 |
            | offline   | 3         | offline         | online          | 0.0 | 0.0 | 0.0 | 2.2 | 2.0  | 2.0 | 0.0 |


    @ups-battery
    @snmp-interface
    Scenario Outline: Load on UPS affects time remaining
            """Battery drain may be faster/slower depending on how much power is drawn from the ups"""

        # Do the usual model pre-setup
        Given Outlet asset with key "1" is created
        And Lamp asset with key "3", minimum "109" Voltage and "120" Wattage is created
        And Lamp asset with key "4", minimum "109" Voltage and "120" Wattage is created

        And asset "1" powers target "190"
        And asset "1903" powers target "3"
        And asset "1904" powers target "4"

        # runtime graph: (120 lamp wattage plus UPS wattage (24 watts))
        And UPS "190" has the following runtime graph
            | wattage | minutes |
            | 24      | 13      |
            | 144     | 60      |
            | 264     | 30      |

        And Engine is up and running

        # toggle lamp states
        When asset "3" goes "<lamp-3>"
        When asset "4" goes "<lamp-4>"

        Then UPS "190" time remaining for battery is "<runtime>" minutes

        Examples: Leaf-node lamp power changes with absent top-parent power source
            | lamp-3  | lamp-4  | runtime |
            | online  | online  | 30      |
            | offline | online  | 60      |
            | offline | offline | 13      |