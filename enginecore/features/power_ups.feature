@ups-asset
@power-behaviour
@state-behaviour
Feature: UPS goes offline when it runs out of battery
    UPS battery is draining when input power source is absent and when charge
    hits zero, UPS should switch to offline state. Conversely, it goes back online
    when power source is restored (and battery charge starts).

    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created
        And UPS asset with key "8" and "1024" port is created
        And asset "1" powers target "8"

        And Lamp asset with key "3", minimum "109" Voltage and "120" Wattage is created
        And Lamp asset with key "4", minimum "109" Voltage and "120" Wattage is created
        And Lamp asset with key "5", minimum "109" Voltage and "120" Wattage is created

        # setup power connections
        And asset "83" powers target "3"
        And asset "84" powers target "4"
        And asset "85" powers target "5"

        And Engine is up and running

    @snmp-behaviour
    Scenario: UPS goes offline on battery drain
        Given UPS "8" battery "drain" factor is set to "10000"
        When asset "1" goes "offline"

        Then after "2" seconds, asset "8" is "offline"
        And SNMP interface for asset "8" is "unreachable"

    @snmp-behaviour
    Scenario: UPS goes online on battery recharge

        # speed up charge/drain processes
        Given UPS "8" battery "drain" factor is set to "10000"
        And UPS "8" battery "charge" factor is set to "10000"

        When asset "1" goes "offline"
        And asset "1" goes "online"

        Then after "2" seconds, asset "8" is "online"
        And SNMP interface for asset "8" is "reachable"

