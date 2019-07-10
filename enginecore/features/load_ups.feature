@draft
@ups-asset
@load-behaviour
@power-behaviour
Feature: UPS Load Handling
    UPS is a special kind of asset that can stop load propagation upstream if
    it is running on battery and there's no input power. Load also affects
    UPS remaining runtime.

    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created
        And UPS asset with key "190" and "1024" port is created
        And Lamp asset with key "3", minimum "109" Voltage and "240" Wattage is created

        # connect together
        And asset "1" powers target "190"
        And asset "1903" powers target "3"

        And Engine is up and running

    Scenario Outline: Load changes across topology

        Given asset "<asset-key>" is "<asset-ini-state>"

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
