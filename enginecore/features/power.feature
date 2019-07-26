@power-behaviour
@state-behaviour
Feature: Power Chaining for Hardware Assets
    This is a set of simple power scenarios where one device can power another.
    Powering down a particular asset can cause a chain reaction of power events
    spread over to the nodes down the power chain.

    Background:
        Given the system model is empty

    Scenario Outline: Simple 3-asset power chain

        # initialize model & engine
        # (1)-[powers]->(2)-[powers]->(3)
        Given Outlet asset with key "1" is created
        And Outlet asset with key "2" is created
        And Lamp asset with key "3", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"
        And asset "2" powers target "3"
        And Engine is up and running
        And asset "<asset-key>" is "<asset-ini-state>"

        # create a certain power condition
        When asset "<asset-key>" goes "<asset-new-state>"

        # check states
        Then asset "1" is "<1>"
        Then asset "2" is "<2>"
        Then asset "3" is "<3>"

        Examples: Downstream power-off chaining
            | asset-key | asset-ini-state | asset-new-state | 1       | 2       | 3       |
            | 1         | online          | offline         | offline | offline | offline |
            | 2         | online          | offline         | online  | offline | offline |
            | 3         | online          | offline         | online  | online  | offline |

        Examples: Downstream power-on chaining
            | asset-key | asset-ini-state | asset-new-state | 1      | 2      | 3      |
            | 1         | offline         | online          | online | online | online |
            | 2         | offline         | online          | online | online | online |
            | 3         | offline         | online          | online | online | online |
