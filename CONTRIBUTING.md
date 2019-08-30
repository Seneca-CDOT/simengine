# Contributing guidelines

## How to become a contributor and submit your own code

### Contributing code

If you have improvements to SimEngine, send us your pull requests! For those
just getting started, Github has a
[how to](https://help.github.com/articles/using-pull-requests/).


### Contribution guidelines and standards

Before sending your pull request, make sure your changes are consistent with the guidelines and follow the coding style.

*   Open an issue per feature/bug (unless one already exists!)
*   Have a branch per issue and follow SimEngine branch name convention
*   Use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0-beta.2/#summary) for formatting your commit messages
*   Use linters such as `pylint` and `eslint`
*   Install & execute code formatters (`black` for `enginecore` and `prettier` for the dashboard)
*   Include tests when you contribute new features (specifically for `enginecore`)
*   Bug fixes also generally require unit tests, because the presence of bugs
    usually indicates insufficient test coverage.


#### Branch name format

Branches should be named as `issues/{issue-num}-{description}` e.g. `issues/101-contrib-docs` where `{issue-num}` is the github issue number associated with changes and `{description}` is a 2-to-3 word description (delimited by `-`);

#### Commit message format

SimEngine switched to [conventional commits](https://www.conventionalcommits.org/en/v1.0.0-beta.2/#summary) for better readability and easy to follow project history.

The commit type can be one of the following:

*   **feat**: A new feature
*   **fix**: A bug fix
*   **docs**: Documentation only changes
*   **refactor**: Code or Structural improvements with no functional changes or fixes
*   **perf**: A code change that improves performance
*   **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
*   **test**: Adding tests
*   **build**: Changes that affect the build system or external dependencies (example scopes: rpm, pip, npm)
*   **ci**: Changes to CI configuration files and scripts
*   **chore**: Anything that does not fit any of the above!


Scope is optional, however, it is best to follow `enginecore` modular structure when used.
For example, use: `cli`, `model`, `hardware`, `engine`, `net`, `tools` etc.
as in `feat(hardware): add network switch asset type`


#### Running Tests

Only `enginecore` supports tests at the moment and instructions on how to run both unittests & BDD-style features can be found on the main enginecore [README.md page](./enginecore/README.md#tests).
