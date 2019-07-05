@draft
Feature: Dual PSU Voltage Handling
    Servers with dual psu have 2 power sources meaning that if
    one source fails, another one takes over the load.

    Scenario: Load is correctly spread over 2 PSUs when both power sources are present
        Given the system model is empty

        # initialize model
        And Outlet asset with key "1" is created
        And Outlet asset with key "2" is created
        And Server asset with key "180", "2" PSU(s) and "480" Wattage is created
        And asset "1" powers target "1801"
        And asset "2" powers target "1802"

        And Engine is up and running

        Then asset "1" load is set to "2.0"
        And asset "2" load is set to "2.0"
