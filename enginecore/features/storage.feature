
# not ci friendly because this requires a VM running (with vm name set in behave.ini)
@not-ci-friendly
@storage-behaviour
@server-asset
@server-bmc-asset
Feature: Storage and storcli64 output
            """
            This is a simple test for making sure that the engine accepts
            supported storcli64 commands & that the return code/response is ok.
            (this does not verify that storcli64 output is *correct though,
            only checks that execution of commands passed through)
            """
    Background:
        Given the system model is empty
        And Outlet asset with key "1" is created

        Given Outlet asset with key "2" is created
        And ServerBMC asset with key "7" and "480" Wattage and storcli64 support is created

        And asset "1" powers target "71"
        And asset "2" powers target "72"

        And Engine is up and running


    Scenario Outline: Storcli commands can be run against a server
        Then response for asset "7" when running storcli64 command "<command>" is ok

        Examples: supported storcli64 commands
            | command                            |
            | storcli64 /c0 show perfmode        |
            | storcli64 /c0 show bgirate         |
            | storcli64 /c0 show ccrate          |
            | storcli64 /c0 show rebuildrate     |
            | storcli64 /c0 show prrate          |
            | storcli64 /c0 show alarm           |
            | storcli64 /c0 show all             |
            | storcli64 /c0 /bbu show all        |
            | storcli64 /c0 /cv show all         |
            | storcli64 /c0 /vall show all       |
            | storcli64 /c0 /eall /sall show all |

