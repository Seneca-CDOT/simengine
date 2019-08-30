# enginecore

`enginecore` is the engine itself written in Python3. It is running in the background as an event loop, supporting all the state/interface simulations and manipulation.

### Project Structure

```bash
├── app.py          # main daemon for the event loop (starting point of the app)
├── simengine-cli   # command line interface to the engine (see simengine-cli -h)
├── script          # various helper scripts (debugging/evalsha for redis etc.)
│
│   # main engine module
├── enginecore
│   ├── cli          # implementation of cli commands (see simengine-cli -h)
│   ├── model        # tools for modelling system topology
│   │   └── presets  # default model parameters for hardware devices (can be overwritten with cli)
│   ├── state        # state handling/manipulation
│   │   ├── agent    # snmp/ipmi/storcli64 simulators
│   │   ├── api      # state api for hardware
│   │   ├── engine   # engine implementation (events/iterations/event loop)
│   │   ├── hardware # hardware behaviour
│   │   ├── net      # websocket interface
│   │   └── sensor   # ipmi sensors
│   └── tools        # utilities including state recorder & randomizer
│
│   # Project tests
├── features   # BDD tests with gherkin-style scenarios/python implementation
├── tests      # unittests
│
│   # MISC tools/data used by the agent simulating network interfaces (SNMP/IPMI)
├── ipmi_sim          # plugin library for ipmi_sim
├── ipmi_template     # sensor templates for ipmi_sim
└── storcli_template  # output templates for storcli64 commands
```

## Installation

### Installing for Development

See development [environment setup page](https://simengine.readthedocs.io/en/latest/Installation/#development-version) on how to install all the relevant packages and configure database.

Install python packages used by `enginecore` modules (production dependencies):

```bash
python3 -m pip install -r requirements.txt
```

Install packages used in testing & development:

```bash
python3 -m pip install -r dev-requirements.txt
```

### Installing for Production Use

Instructions on how to install SimEngine packaged as .rpm can be found [here](https://simengine.readthedocs.io/en/latest/Installation/#release-rpm).

## Running

The main app daemon can be run as:

```bash
/usr/bin/python3 ./app.py -d -r -v
```

**Note**: using some UDP ports (161) requires sudo privileges.

Or it can be managed as a service if built from an [RPM](https://simengine.readthedocs.io/en/latest/Installation/#release-rpm);

```bash
simengine-core start
```

## Developing for enginecore

### Lint & Format

PyLint can be installed with:

`sudo python3 -m pip install pylint`

SimEngine [lintrc](./.pylintrc) file is based on Google Style Guide. See this docstring [example](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for documentation format reference.

SimEngine is using [black](https://github.com/psf/black) code formatter for python3 which is (most-likely) supported in your favorite IDE.

For example, a VSCode configuration could include:

```javascript
{
    "files.autoSave": "onFocusChange",
    "editor.formatOnSave": true,
    "python.formatting.provider": "black",
    ...
}
```

to make formatting easy and automated (this requires [official python VSCode extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)).

It is recommended to install `pre-commit` hooks to simplify formatting and issues identification on `git commit`:

```bash
pre-commit install
```

### Tests

Two testing frameworks are in use: **unittest** (standard python testing module) and **behave** for [BDD-style](https://behave.readthedocs.io/en/latest/) scenarios.

### UnitTests

For now, unittests are only used for the engine [tools](./enginecore/tools) (which includes action Randomizer, Recorder and other utilities) and can be run with:

```bash
python3 -m unittest discover -s ./tests -p test_*.py
```

### Behave

BDD tests are oriented towards testing various engine components (hardware assets), behaviour in general (power, thermal behaviour etc.) or simulated network interfaces returning expected data (IPMI/SNMP).

You can run tests as:

```bash
python3 -m behave ./features/ -k --stop --no-capture-stderr
```

**Note**: running tests requires a VM with a domain name `test-ipmi` and [proper .xml configurations](https://simengine.readthedocs.io/en/latest/Assets%20Configurations/#server-type) (alternatively, you can update [vm name in the config file](./behave.ini)).

You can also control which tests you want to run by using tags, for example this command will test only
scenarios associated with UPS features and it will ignore tests that are slow to run:

```bash
python3 -m behave ./features/ -k --stop --no-capture-stderr --tags=@ups-asset --tags=~@slow
```

Here is the list of tags & their use:

| tag                | purpose                                                                                     |
| ------------------ | ------------------------------------------------------------------------------------------- |
| @quick-test        | test simple & quick scenarios for power/voltage/load                                        |
| @power-behaviour   | tests associated with power                                                                 |
| @voltage-behaviour | tests associated with voltage (drop/increase etc)                                           |
| @thermal-behaviour | tests associated with temperature and thermal aspects of simulation                         |
| @load-behaviour    | tests associated with amperage and load distribution in the system                          |
| @storage-behaviour | tests associated with storage & storcli64                                                   |
| @ipmi-interface    | check that the simulated BMC returns correct & expected values through IPMI                 |
| @snmp-interface    | check that snmpsimd is returning correct values through snmp interface                      |
| @ups-asset         | all tests associated with UPS hardware                                                      |
| @pdu-asset         | all tests associated with PDU hardware                                                      |
| @server-asset      | test server hardware behaviour                                                              |
| @server-bmc-asset  | all tests associated with server that supports bmc                                          |
| @dual-psu-asset    | all tests associated with assets supporting multiple power sources                          |
| @slow              | tests that may take some time to run                                                        |
| @not-ci-friendly   | not recommended for integration testing due to extra dependencies or other reasons          |
| @unreliable        | tests that rely on delays (e.g. ipmi_sim polls files at certain rates) or that behave weird |
| @corner-case       | some nasty corner case that needs extra attention                                           |

You can also mark tests for work-in-progress by attaching `@wip` tag to a scenario or feature.

It may be convenient to set up an alias as:

```bash
alias behave-well='python3 -m behave ./features/ -k --stop --no-capture-stderr'
```
