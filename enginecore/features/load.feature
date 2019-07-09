@draft
Feature: Load handling and distribution across entire system tolology

    Load travels uptream and it may change due to either voltage spikes/drops or power update
    of hardware assets.

    Background:
        Given the system model is empty

    @power-behaviour
    Scenario Outline: Upstream load changes when assets are powered off/on

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
        Then asset "1" load is set to "<1>"
        Then asset "2" load is set to "<2>"
        Then asset "3" load is set to "<3>"

        Examples: Load drop due to power changes (something powered off)
            | asset-key | asset-ini-state | asset-new-state | 1   | 2   | 3   |
            | 1         | online          | offline         | 0.0 | 0.0 | 0.0 |
            | 2         | online          | offline         | 0.0 | 0.0 | 0.0 |
            | 3         | online          | offline         | 0.0 | 0.0 | 0.0 |

        Examples: Load spike due to power changes  (something powered on)
            | asset-key | asset-ini-state | asset-new-state | 1   | 2   | 3   |
            | 1         | offline         | online          | 1.0 | 1.0 | 1.0 |
            | 2         | offline         | online          | 1.0 | 1.0 | 1.0 |
            | 3         | offline         | online          | 1.0 | 1.0 | 1.0 |

    @power-behaviour
    Scenario Outline: Zero load across the system
            """(this is to verify that enigne doesn't get stuck waiting for load branches to complete)"""
        # initialize model & engine
        # (1)-[powers]->(2)-[powers]->(3)
        Given Outlet asset with key "1" is created
        And Outlet asset with key "2" is created
        And Outlet asset with key "3" is created

        And asset "1" powers target "2"
        And asset "2" powers target "3"
        And Engine is up and running
        And asset "<asset-key>" is "<asset-ini-state>"

        # create a certain power condition
        When asset "<asset-key>" goes "<asset-new-state>"

        # check states
        Then asset "1" load is set to "<1>"
        Then asset "2" load is set to "<2>"
        Then asset "3" load is set to "<3>"

        Examples: Same load & nothing changes (even though something powered off)
            | asset-key | asset-ini-state | asset-new-state | 1   | 2   | 3   |
            | 1         | online          | offline         | 0.0 | 0.0 | 0.0 |
            | 2         | online          | offline         | 0.0 | 0.0 | 0.0 |
            | 3         | online          | offline         | 0.0 | 0.0 | 0.0 |

        Examples: Same load & nothing changes (even though something powered up)
            | asset-key | asset-ini-state | asset-new-state | 1   | 2   | 3   |
            | 1         | offline         | online          | 0.0 | 0.0 | 0.0 |
            | 2         | offline         | online          | 0.0 | 0.0 | 0.0 |
            | 3         | offline         | online          | 0.0 | 0.0 | 0.0 |


