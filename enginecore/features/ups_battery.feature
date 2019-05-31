Feature: UPS Voltage Handling
    Voltage may affect UPS state,
    input voltage that is below or above the defined thresholds
    will cause UPS transfer to battery.

    @snmp-behaviour
    Scenario: Voltage drops slightly below low threshold thus causing brownout
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage "120" drops below "AdvConfigLowTransferVolt" threshold by "10"
        Then UPS is on battery
        And UPS transfer reason is set to "smallMomentarySag"
        And after "5" seconds, the transfer reason is set to "brownout"

    @snmp-behaviour
    Scenario: Voltage drops below low threshold thus causing blackout
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage "120" drops below "AdvConfigLowTransferVolt" threshold by "100"
        Then UPS is on battery
        And UPS transfer reason is set to "deepMomentarySag"
        And after "5" seconds, the transfer reason is set to "blackout"

    @snmp-behaviour
    Scenario: Voltage spikes above high-threshold
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage "120" spikes above "AdvConfigHighTransferVolt" threshold by "10"
        Then UPS is on battery
        And UPS transfer reason is set to "highLineVoltage"

    @snmp-behaviour
    Scenario: Voltage drops below threshold and then spikes back to normal
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage "120" drops below "AdvConfigLowTransferVolt" threshold by "10"
        And voltage is set to "110"
        Then UPS is not on battery
        And UPS transfer reason is set to "noTransfer"


    @snmp-behaviour
    Scenario: Voltage spikes above threshold and then drops back to normal
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage "120" spikes above "AdvConfigHighTransferVolt" threshold by "10"
        And voltage is set to "110"
        Then UPS is not on battery
        And UPS transfer reason is set to "noTransfer"

    @snmp-behaviour
    Scenario: Voltage drops below threshold and then spikes above threshold
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage is set to "0"
        And voltage "0" spikes above "AdvConfigHighTransferVolt" threshold by "10"
        Then UPS is on battery
        And UPS transfer reason is set to "highLineVoltage"

