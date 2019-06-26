Feature: Power Chaining for Hardware Assets
    Simple 2-asset power scenarios involving a lamp and an outlet powering it;



    @power-behaviour
    Scenario: 3 Hardware assets case
        Given the system model is empty

        # initialize model
        And Outlet asset with key "1" is created
        And Outlet asset with key "2" is created
        And Lamp asset with key "3", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"
        And asset "2" powers target "3"

        And Engine is up and running

        # check state
        # Then asset "1" load is set to "1.0"
        # And asset "2" load is set to "1.0"
        Then asset "1" is online
        And asset "2" is online
        And asset "3" is online


    @power-behaviour
    Scenario: Lamp is on and it's drawing power
        Given the system model is empty

        # initialize model
        And Outlet asset with key "1" is created
        And Lamp asset with key "2", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"

        And Engine is up and running

        # check state
        # Then asset "1" load is set to "1.0"
        # And asset "2" load is set to "1.0"
        Then asset "1" is online
        And asset "2" is online

    @power-behaviour
    Scenario: Lamp goes offline
        Given the system model is empty

        # initialize model
        And Outlet asset with key "1" is created
        And Lamp asset with key "2", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"

        And Engine is up and running

        When asset "2" is powered down

        # check state
        Then asset "1" load is set to "0.0"
        And asset "2" load is set to "0.0"
        And asset "1" is online
        And asset "2" is offline

    @power-behaviour
    Scenario: Lamp goes offline and back online
        Given the system model is empty

        # initialize model
        And Outlet asset with key "1" is created
        And Lamp asset with key "2", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"

        And Engine is up and running

        When asset "2" is powered down
        And asset "2" is powered up

        # check state
        Then asset "1" load is set to "1.0"
        And asset "2" load is set to "1.0"
        And asset "1" is online
        And asset "2" is online


    @power-behaviour
    Scenario: Outlet goes offline
        Given the system model is empty

        # initialize model
        And Outlet asset with key "1" is created
        And Lamp asset with key "2", minimum "109" Voltage and "120" Wattage is created
        And asset "1" powers target "2"

        And Engine is up and running

        When asset "1" is powered down

        # check state
        Then asset "1" load is set to "0.0"
        And asset "2" load is set to "0.0"
        And asset "1" is offline
        And asset "2" is offline


