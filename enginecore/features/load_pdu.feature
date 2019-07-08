@draft
@sequential
Feature: Load distribution with assets that have multiple children

    Load for a parent device that has multiple child nodes powered by it
    is the sum of all the child nodes load

    Background:
        Given the system model is empty

    @power-behaviour
    Scenario Outline: Multiple children load chain

        # == initialize model & engine ==
        # (1)-[powers]->(2)-[powers]->(3, 4, 5)
        Given Outlet asset with key "1" is created
        And PDU asset with key "7",  minimum "105" Voltage and "1025" port is created

        And Lamp asset with key "3", minimum "109" Voltage and "120" Wattage is created
        And Lamp asset with key "4", minimum "109" Voltage and "120" Wattage is created
        And Lamp asset with key "5", minimum "109" Voltage and "120" Wattage is created

        # setup power connections
        And asset "1" powers target "7"
        And asset "73" powers target "3"
        And asset "74" powers target "4"
        And asset "75" powers target "5"

        And Engine is up and running
        And asset "<asset-key>" is "<asset-ini-state>"

        # create a certain power condition
        When asset "<asset-key>" goes "<asset-new-state>"

        # == check states ==
        Then asset "1" load is set to "<1>"

        # PDU & its outlets
        Then asset "7" load is set to "<7>"
        Then asset "73" load is set to "<73>"
        Then asset "74" load is set to "<74>"
        Then asset "75" load is set to "<75>"

        # everythin powered by the PDU
        Then asset "3" load is set to "<3>"
        Then asset "4" load is set to "<4>"
        Then asset "5" load is set to "<5>"

        Examples: Check load on start
            | asset-key | asset-ini-state | asset-new-state | 1   | 7   | 73  | 74  | 75  | 3   | 4   | 5   |
            | 1         | online          | online          | 3.0 | 3.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

        Examples: Load drop due to power changes
            | asset-key | asset-ini-state | asset-new-state | 1   | 7   | 73  | 74  | 75  | 3   | 4   | 5   |
            | 1         | online          | offline         | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
            | 7         | online          | offline         | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
            | 73        | online          | offline         | 2.0 | 2.0 | 0.0 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 |
            | 75        | online          | offline         | 2.0 | 2.0 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 0.0 |

        Examples: Load increase due to power changes
            | asset-key | asset-ini-state | asset-new-state | 1   | 7   | 73  | 74  | 75  | 3   | 4   | 5   |
            | 1         | offline         | online          | 3.0 | 3.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
            | 7         | offline         | online          | 3.0 | 3.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
            | 73        | offline         | online          | 3.0 | 3.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
            | 75        | offline         | online          | 3.0 | 3.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |