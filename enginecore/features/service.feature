Feature: UPS Voltage Handling
    Voltage may affect UPS state,
    input voltage that is below or above the defined thresholds
    will cause UPS transfer to battery.

    @snmp-behaviour
    Scenario: Voltage drops slightly below low threshold thus causing brownout
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage drops below "AdvConfigLowTransferVolt" threshold by "10"
        Then ups transfers to battery with reason "smallMomentarySag"
        And after "5" seconds, the transfer reason is set to "brownout"

    @snmp-behaviour
    Scenario: Voltage drops below low threshold thus causing blackout
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage drops below "AdvConfigLowTransferVolt" threshold by "100"
        Then ups transfers to battery with reason "deepMomentarySag"
        And after "5" seconds, the transfer reason is set to "blackout"

    @snmp-behaviour
    Scenario: Voltage spikes above high-threshold
        Given the system model is empty
        And UPS asset with key "190" is created
        When voltage spikes above "AdvConfigHighTransferVolt" threshold by "10"
        Then ups transfers to battery with reason "highLineVoltage"