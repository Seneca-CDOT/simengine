Feature: Power Chaining for Hardware Assets
    Testing simple power scenarios where one device can power another.
    Powering down a particular asset can cause a chain reaction of power events
    spread over to its children

    @power-behaviour
    Scenario Outline: Child-node assets react to the changes in their parent power states, simple 3-asset power chain
        Given the system model is empty

        # initialize model & engine
        And Outlet asset with key "1" is created
        And Outlet asset with key "2" is created
        And Lamp asset with key "3", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"
        And asset "2" powers target "3"
        And Engine is up and running
        And asset "<asset-key>" is "<asset-ini-state>"

        # create a certain power condition
        When asset "<asset-key>" goes "<asset-new-state>"

        # check states
        Then asset "1" is <1-state>
        Then asset "2" is <2-state>
        Then asset "3" is <3-state>

        Examples: Downstream power-off chaining: (1)-[powers]->(2)-[powers]->(3)
            | asset-key | asset-ini-state | asset-new-state | 1-state | 2-state | 3-state |
            | 1         | online          | offline         | offline | offline | offline |
            | 2         | online          | offline         | online  | offline | offline |
            | 3         | online          | offline         | online  | online  | offline |

        Examples: Downstream power-on chaining: (1)-[powers]->(2)-[powers]->(3)
            | asset-key | asset-ini-state | asset-new-state | 1-state | 2-state | 3-state |
            | 1         | offline         | online          | online  | online  | online  |
            | 2         | offline         | online          | online  | online  | online  |
            | 3         | offline         | online          | online  | online  | online  |