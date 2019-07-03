@sequential
Feature: Power Chaining for Hardware Assets
    Testing simple power scenarios where one device can power another.
    Powering down a particular asset can cause a chain reaction of power events
    spread over to its children

    Background:
        Given the system model is empty

    @power-behaviour
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

    @power-behaviour
    Scenario Outline: Multiple children power chain

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
        Then asset "1" is "<1>"

        # PDU & its outlets
        Then asset "7" is "<7>"
        Then asset "73" is "<73>"
        Then asset "74" is "<74>"
        Then asset "75" is "<75>"

        # everythin powered by the PDU
        Then asset "3" is "<3>"
        Then asset "4" is "<4>"
        Then asset "5" is "<5>"

        Examples: Downstream power-off chaining
            | asset-key | asset-ini-state | asset-new-state | 1       | 7       | 73      | 74      | 75      | 3       | 4       | 5       |
            | 1         | online          | offline         | offline | offline | offline | offline | offline | offline | offline | offline |
            | 7         | online          | offline         | online  | offline | offline | offline | offline | offline | offline | offline |
            | 73        | online          | offline         | online  | online  | offline | online  | online  | offline | online  | online  |
            | 75        | online          | offline         | online  | online  | online  | online  | offline | online  | online  | offline |

        Examples: Downstream power-on chaining
            | asset-key | asset-ini-state | asset-new-state | 1      | 7      | 73     | 74     | 75     | 3      | 4      | 5      |
            | 1         | offline         | online          | online | online | online | online | online | online | online | online |
            | 7         | offline         | online          | online | online | online | online | online | online | online | online |
            | 73        | offline         | online          | online | online | online | online | online | online | online | online |
            | 75        | offline         | online          | online | online | online | online | online | online | online | online |

