@voltage-behaviour
@power-behaviour
@quick-test
Feature: System handles voltage updates
    Voltage may affect asset states by causing them to power off (if underpowered)
    or back up (AC restored)
    Voltage Event is propagated down the power stream

    Background:
        Given the system model is empty
        # initialize model & engine
        # (1)-[powers]->(2)-[powers]->(3)
        Given Outlet asset with key "1" is created
        And Outlet asset with key "2" is created
        And Lamp asset with key "3", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"
        And asset "2" powers target "3"
        And Engine is up and running

    Scenario Outline: Voltage affecting assets' states

        Given wallpower voltage is set to "<ini-volt>"
        # create a certain power condition
        When wallpower voltage is updated to "<new-volt>"

        # check states
        Then asset "1" is "<1-state>"
        And asset "2" is "<2-state>"
        And asset "3" is "<3-state>"

        Examples: Downstream voltage drop chaining
            | ini-volt | new-volt | 1-state | 2-state | 3-state |
            | 120      | 0        | offline | offline | offline |
            | 120      | 110      | online  | online  | online  |
            | 120      | 108      | online  | online  | offline |

        Examples: Downstream voltage increase chaining
            | ini-volt | new-volt | 1-state | 2-state | 3-state |
            | 0        | 120      | online  | online  | online  |
            | 0        | 110      | online  | online  | online  |
            | 0        | 100      | online  | online  | offline |

    Scenario Outline: Input/Output voltage for assets

        Given wallpower voltage is set to "<ini-volt>"
        # create a certain power condition
        When wallpower voltage is updated to "<new-volt>"

        # check states
        Then asset "1" input voltage is "<1-in-volt>"
        Then asset "1" output voltage is "<1-out-volt>"

        Then asset "2" input voltage is "<2-in-volt>"
        Then asset "2" output voltage is "<2-out-volt>"

        Then asset "3" input voltage is "<3-in-volt>"
        Then asset "3" output voltage is "<3-out-volt>"


        Examples: Downstream voltage drop chaining
            | ini-volt | new-volt | 1-in-volt | 1-out-volt | 2-in-volt | 2-out-volt | 3-in-volt | 3-out-volt |
            | 120      | 0        | 0         | 0          | 0         | 0          | 0         | 0          |
            | 120      | 110      | 110       | 110        | 110       | 110        | 110       | 110        |
            | 120      | 108      | 108       | 108        | 108       | 108        | 108       | 0          |

    @corner-case
    Scenario: Voltage changes are ignored when an outlet is turned off by a user
        Given asset "1" is "offline"
        And wallpower voltage is set to "80"

        When wallpower voltage is updated to "120"

        # asset state should not change despite voltage update
        Then asset "1" is "offline"
        And asset "2" is "offline"
        And asset "3" is "offline"
