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
        And Engine is up and running

    @power-behaviour
    @snmp-interface
    Scenario Outline: Voltage drops below lower thresholds thus causing battery transfer
        When voltage "<input-volt>" drops below "<threshold>" threshold by "<drops-by>" for UPS "190"

        # State checks for ups
        Then UPS "190" is "<battery-status>" battery
        And UPS "190" transfer reason is set to "<transfer-reason>"
        And after "5" seconds, transfer reason for UPS "190" is "<transfer-reason-delayed>"

        Examples: UPS input voltage changes
            | input-volt | threshold                | drops-by | battery-status | transfer-reason   | transfer-reason-delayed |
            | 120        | AdvConfigLowTransferVolt | 10       | on             | smallMomentarySag | brownout                |
            | 120        | AdvConfigLowTransferVolt | 100      | on             | deepMomentarySag  | blackout                |

    @power-behaviour
    @snmp-interface
    Scenario Outline: Voltage spikes above upper thresholds thus causing battery transfer
        When voltage "<input-volt>" spikes above "<threshold>" threshold by "<spikes-by>" for UPS "190"

        # State checks for ups
        Then UPS "190" is "<battery-status>" battery
        And UPS "190" transfer reason is set to "<transfer-reason>"

        Examples: UPS input voltage changes
            | input-volt | threshold                 | spikes-by | battery-status | transfer-reason |
            | 120        | AdvConfigHighTransferVolt | 10        | on             | highLineVoltage |
