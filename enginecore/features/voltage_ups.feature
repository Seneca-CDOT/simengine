@ups-asset
@voltage-behaviour
@power-behaviour
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

    @snmp-interface
    @ups-battery
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

    @snmp-interface
    @ups-battery
    Scenario Outline: Voltage spikes above upper thresholds thus causing battery transfer
        When voltage "<input-volt>" spikes above "<threshold>" threshold by "<spikes-by>" for UPS "190"

        # State checks for ups
        Then UPS "190" is "<battery-status>" battery
        And UPS "190" transfer reason is set to "<transfer-reason>"

        Examples: UPS input voltage changes
            | input-volt | threshold                 | spikes-by | battery-status | transfer-reason |
            | 120        | AdvConfigHighTransferVolt | 10        | on             | highLineVoltage |

    @snmp-interface
    @ups-battery
    Scenario Outline: Voltage causes UPS change back and forth to battery/input power
        When wallpower voltage is updated to "<volt-1>"
        And wallpower voltage is updated to "<volt-2>"
        And wallpower voltage is updated to "<volt-3>"

        Then UPS "190" is "<battery-status>" battery
        And UPS "190" transfer reason is set to "<transfer-reason>"

        Examples: From battery back to normal input power source
            | volt-1 | volt-2 | volt-3 | battery-status | transfer-reason |
            | 120    | 20     | 110    | not on         | noTransfer      |
            | 120    | 140    | 115    | not on         | noTransfer      |
            | 0      | 140    | 120    | not on         | noTransfer      |
            | 120    | 0      | 120    | not on         | noTransfer      |


        Examples: Changes from one transfer cause to another
            | volt-1 | volt-2 | volt-3 | battery-status | transfer-reason |
            | 120    | 0      | 140    | on             | highLineVoltage |
            | 120    | 200    | 0      | on             | blackout        |

    Scenario: Voltage propagation is blocked when UPS is running on battery
        When wallpower voltage is updated to "90"
        And wallpower voltage is updated to "70"
        And wallpower voltage is updated to "80"

        # check states
        Then asset "190" input voltage is "80"
        And asset "190" output voltage is "120"

        Then asset "1901" input voltage is "120"
        And asset "1901" output voltage is "120"


    Scenario: Voltage propagation works when UPS is not on battery
        When wallpower voltage is updated to "118"
        And wallpower voltage is updated to "122"

        # check states
        Then asset "190" input voltage is "122"
        And asset "190" output voltage is "122"

        Then asset "1901" input voltage is "122"
        And asset "1901" output voltage is "122"
