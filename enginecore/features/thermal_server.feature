
# not ci friendly because this requires a VM running (with vm name set in behave.ini)
@not-ci-friendly
@server-asset
@thermal-behaviour
@server-bmc-asset
@ipmi-interface
Feature: Internal thermal behaviour for Server's sensors
    ServerBMC supports thermal sensors such as CPU, PSU temperatures etc.
    These sensors are affected by ambient changes in the server rack and can also
    be subjected to heating/cooling from other components (CPU load, PSU etc.)

    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created

    Scenario: Thermal sensors get updated with ambient temperature
        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"
        And Engine is up and running

        When ambient is set to "24" degrees
        # ipmi_sim reads from a file with a delay
        And pause for "2" seconds

        Then asset "7" BMC sensor "CPU1 temperature" value is "24 degrees C"