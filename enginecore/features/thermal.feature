# @simengine-cli
@thermal-behaviour
Feature: Ambient temperature changes
    Ambient starts rising on power outages and may affect states of hardware
    (e.g. temperature sensors of BMC servers)

    Background:
        Given the system model is empty

    Scenario Outline: Ambient goes up on power outage

        # give some initial state conditions
        Given Engine is up and running
        And server room has the following ambient properties
            | event | degrees | rate | pause_at |
            | down  | 1       | 1    | 22       |


        And ambient is "21" degrees

        # simulate power outage
        When power outage happens

        Then ambient rises to "22" after "3" seconds
