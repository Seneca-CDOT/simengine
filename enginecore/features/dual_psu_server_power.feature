Feature: Dual PSU Voltage Handling
    Servers with dual psu have 2 power sources meaning that if
    one source fails, another one takes over the load.

    Scenario: Load is correctly spread over 2 PSUs when both power sources are present
        Given the system model is empty
        And Server asset with key "180", "2" PSU(s) and "480" Wattage is created
        And Engine is up and running