@draft
Feature: UPS Voltage Handling
    Voltage may affect UPS state,
    input voltage that is below or above the defined thresholds
    will cause UPS transfer to battery.

    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created
        And UPS asset with key "190" and "1024" port is created
        And asset "1" powers target "190"

    @power-behaviour
    @snmp-interface
    Scenario Outline: UPS voltage threshold checks
        Given Engine is up and running
        When voltage "<input-volt>" drops below "<threshold>" threshold by "<drops-by>" for UPS "190"

        # State checks for ups
        Then UPS "190" is "<battery-status>" battery
        And UPS "190" transfer reason is set to "<transfer-reason>"

        Examples: UPS input voltage changes
            | input-volt | threshold                | drops-by | battery-status | transfer-reason   |
            | 120        | AdvConfigLowTransferVolt | 10       | on             | smallMomentarySag |
