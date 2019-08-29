@thermal-behaviour
Feature: Ambient temperature changes
    Ambient starts rising on power outages and may affect states of hardware
    (e.g. temperature sensors of BMC servers)

    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created
        And Outlet asset with key "2" is created
        And UPS asset with key "190" and "1024" port is created
        And asset "1" powers target "2"
        And asset "2" powers target "190"

    Scenario: Ambient is set to 21 degrees on engine start
        Given Engine is up and running
        Then ambient is set to "21" degrees

    @power-behaviour
    Scenario: Ambient goes up on power outage

        # give some initial state conditions
        Given server room has the following ambient properties
            | event | degrees | rate | pause_at |
            | down  | 1       | 1    | 22       |
            | up    | 1       | 1    | 21       |

        And Engine is up and running
        And ambient is "21" degrees

        # simulate power outage
        When power outage happens

        Then ambient is set to "22" after "3" seconds

    @power-behaviour
    Scenario: Ambient goes down when power is restored
        # give some initial state conditions
        Given server room has the following ambient properties
            | event | degrees | rate | pause_at |
            | down  | 1       | 1    | 22       |
            | up    | 1       | 1    | 19       |

        And Engine is up and running
        And ambient is "21" degrees

        # simulate power outage
        When power outage happens
        And power is restored

        Then ambient is set to "19" after "3" seconds

