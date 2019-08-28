@ups-asset
@power-behaviour
@state-behaviour

# not-ci-friendly because this test case relies on hardcoded delay
# (e.g. in 'Then after "n" seconds, ...') to wait for battery to
# deplete completely; (would be better to implement circuits hook like
# AllLoadBranchesDone but for battery depletion, so that step implementation
# can wait for it to finish instead of relying on n-second delay)
@not-ci-friendly
Feature: UPS goes offline when it runs out of battery
    UPS battery is draining when input power source is absent and when charge
    hits zero, UPS should switch to offline state. Conversely, it goes back online
    when power source is restored (and battery charge starts).

    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created
        And UPS asset with key "8" and "1024" port is created
        And asset "1" powers target "8"

        And Engine is up and running

    @snmp-behaviour
    Scenario: UPS goes offline on complete battery drain
        Given UPS "8" battery "drain" factor is set to "10000"
        When asset "1" goes "offline"

        # commented out since testing this requires redis_state_hander running
        # since UPS publishes state changes through redis pub/sub
        # Then after "2" seconds, asset "8" is "offline"

        Then after "4" seconds, SNMP interface for asset "8" is "unreachable"

    @snmp-behaviour
    Scenario: UPS goes online on battery recharge (with 0 battery level)

        # speed up charge/drain processes
        Given UPS "8" battery "drain" factor is set to "10000"
        And UPS "8" battery "charge" factor is set to "10000"

        When asset "1" goes "offline"
        And asset "1" goes "online"

        Then after "2" seconds, asset "8" is "online"
        And SNMP interface for asset "8" is "reachable"

    @snmp-interface
    @ups-battery
    Scenario Outline: Battery charge/drain is launched when UPS state changes

        Given UPS "8" battery "drain" factor is set to "70"
        And UPS "8" battery "charge" factor is set to "70"
        And asset "1" is "<ps-ini-state>"

        # Toggle UPS state
        When asset "1" goes "<ps-new-state>"
        And asset "8" goes "<ups-ini-state>"
        And asset "8" goes "<ups-new-state>"

        Then UPS "8" is "<battery-status>" battery
        And UPS "8" battery is "<battery-charge-status>"

        Examples: UPS starts battery drain when powered on with no power source
            | ps-ini-state | ps-new-state | ups-ini-state | ups-new-state | battery-status | battery-charge-status |
            | offline      | offline      | offline       | online        | on             | draining              |

        Examples: UPS starts battery charge when powered on with power source online
            | ps-ini-state | ps-new-state | ups-ini-state | ups-new-state | battery-status | battery-charge-status |
            | online       | online       | offline       | online        | not on         | inactive              |
            | offline      | online       | offline       | online        | not on         | charging              |


