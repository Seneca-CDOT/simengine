import React, { Fragment } from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

// Material imports
import { withStyles } from '@material-ui/core/styles';
import { AppBar, Toolbar, Typography } from '@material-ui/core';

// local imports
import SettingsOption from './SettingsOption';
import SysStatusOption from './SysStatusOption';

class TopNav extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      ambientRising: false,
      lastTempChange: new Date(),
      flash: false,
    };

    this.flashArrow = null;
  }

  componentWillReceiveProps(newProps) {
    /** Flash temperature arrow */

    if (newProps.ambient == this.props.ambient) {
      return;
    }
    const elapsedSinceLastTemp = new Date() - this.state.lastTempChange;

    clearInterval(this.flashArrow);

    // flash arrow icon on temp changes
    this.flashArrow = setInterval(() => {
      this.setState(() => ({ flash: true }));
      setTimeout(() => {
        this.setState(() => ({ flash: false }));
      }, elapsedSinceLastTemp * 0.5 * 0.8);
    }, elapsedSinceLastTemp * 0.5);

    // stop flashing arrow after a while (max is 1 minute)
    const maxFlashingTime = 60 * 1000;

    setTimeout(
      () => {
        clearInterval(this.flashArrow);
        this.setState({ flash: false, ambientRising: false });
      },
      elapsedSinceLastTemp > maxFlashingTime
        ? maxFlashingTime
        : elapsedSinceLastTemp,
    );

    this.setState({
      ambientRising: newProps.ambientRising,
      lastTempChange: new Date(),
    });
  }

  render() {
    const { classes } = this.props;

    return (
      <Fragment>
        <AppBar
          position="absolute"
          className={classNames(classes.appBar, classes[`appBar-left`])}
        >
          <Toolbar>
            <Typography variant="title" color="inherit" noWrap>
              HAos Simulation Engine
            </Typography>
            {/* Gear openning a drawer */}
            <div className={classes.grow}>
              <SettingsOption
                saveLayout={this.props.saveLayout}
                executePlay={this.props.executePlay}
                plays={this.props.plays}
              />
            </div>

            {/* Top-right nav options*/}
            <div>
              <SysStatusOption
                mainsStatus={this.props.mainsStatus}
                togglePower={this.props.togglePower}
                ambient={this.props.ambient}
                flash={this.state.flash}
                ambientRising={this.state.ambientRising}
              />
            </div>
          </Toolbar>
        </AppBar>
      </Fragment>
    );
  }
}

const styles = {
  grow: {
    flexGrow: 1,
  },
  appBar: {
    width: `100%`,
  },
  'appBar-left': {
    backgroundColor: '#36454F',
    marginLeft: 240,
  },
};

TopNav.propTypes = {
  /** styling */
  classes: PropTypes.object,
  /** current room temp */
  ambient: PropTypes.number.isRequired,
  /** indicates if room temp is going up */
  ambientRising: PropTypes.bool.isRequired,
  /** mains power source status */
  mainsStatus: PropTypes.bool.isRequired,
  /** collection of executable scripts */
  plays: PropTypes.array,
  /** mains toggle callback */
  togglePower: PropTypes.func.isRequired,
  /** drawer Save Layout callback */
  saveLayout: PropTypes.func.isRequired,
  /** execute playbook callback */
  executePlay: PropTypes.func.isRequired,
};

export default withStyles(styles)(TopNav);
