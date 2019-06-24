Feature: Power Chaining for Hardware Assets
    Simple 2-asset power scenarios involving a lamp and an outlet powering it;

    Scenario: Lamp is on and it's drawing power
        Given the system model is empty

        # initialize model
        And Outlet asset with key "1" is created
        And Lamp asset with key "2", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"

        And Engine is up and running

        Then asset "1" load is set to "1.0"
        And asset "2" load is set to "1.0"
        And asset "1" is online
        And asset "2" is online

