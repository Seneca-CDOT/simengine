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

    if (newProps.ambient == this.props.ambient) { return; }
    const elapsedSinceLastTemp = new Date() - this.state.lastTempChange;

    clearInterval(this.flashArrow);

    // flash arrow icon on temp changes
    this.flashArrow = setInterval(() => {
      this.setState(() => ({flash: true}));
      setTimeout(() => {
        this.setState(() => ({flash: false}));
      }, elapsedSinceLastTemp*0.5*0.8);
    }, elapsedSinceLastTemp*0.5);


    // stop flashing arrow after a while (max is 1 minute)
    const maxFlashingTime =  60*1000;

    setTimeout(() => {
      clearInterval(this.flashArrow);
      this.setState({ flash: false, ambientRising: false });

    }, (elapsedSinceLastTemp > maxFlashingTime?maxFlashingTime:elapsedSinceLastTemp));

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
            <div style={styles.grow}>
              <SettingsOption saveLayout={this.props.saveLayout} classes={this.props.classes}/>
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
};

TopNav.propTypes = {
  classes: PropTypes.object, // styling
  saveLayout: PropTypes.func.isRequired, // drawer Save Layout callback
  ambient: PropTypes.number.isRequired, // room temp
  ambientRising: PropTypes.bool.isRequired, // is room temp going up?
  mainsStatus: PropTypes.bool.isRequired, // mains power source status
  togglePower: PropTypes.func.isRequired,
};

export default withStyles(styles)(TopNav);
