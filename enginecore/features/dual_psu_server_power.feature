@not-ci-friendly
Feature: Dual PSU Voltage Handling
    Servers with dual psu have 2 power sources meaning that if
    one source fails, another one takes over the load.

    Scenario: Load is correctly spread over 2 PSUs when both power sources are present
