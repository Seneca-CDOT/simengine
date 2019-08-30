import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import {
  AcUnit,
  PowerSettingsNew,
  ArrowDownward,
  ArrowUpward,
} from '@material-ui/icons';
import { Grid, Typography, Fade } from '@material-ui/core';
import { withStyles } from '@material-ui/core/styles';

// local imports
import PowerSwitch from '../common/PowerSwitch';
import colors from '../../styles/colors';

/**
 * Top-Right Nav options
 */
const SysStatusOption = ({
  mainsStatus,
  ambient,
  ambientRising,
  flash,
  togglePower,
  classes,
}) => {
  return (
    <Grid container>
      {/* Wall power status */}
      <Grid item>
        <PowerSwitch
          checked={mainsStatus}
          onChange={() => togglePower(!mainsStatus)}
          label={
            <Typography variant="title" className={classes.title}>
              <PowerSettingsNew className={classes.inlineIcon} />
              The Mains:
              <span className={mainsStatus ? classes.online : classes.heating}>
                {' '}
                {mainsStatus ? 'online' : 'offline'}
              </span>
            </Typography>
          }
        />
      </Grid>

      {/* Ambient Temperature */}
      <Grid item className={classNames(classes.menuOptions, classes.tempGauge)}>
        <Typography variant="title" color="inherit">
          <AcUnit className={classes.inlineIcon} />
          <span className={ambient > 27 ? classes.heating : classes.cooling}>
            {ambient}°
            <Fade in={flash}>
              {ambientRising ? (
                <ArrowUpward className={classes.inlineIcon} />
              ) : (
                <ArrowDownward className={classes.inlineIcon} />
              )}
            </Fade>
          </span>
        </Typography>
      </Grid>
    </Grid>
  );
};

const styles = {
  inlineIcon: {
    marginRight: '0.3em',
    marginBottom: '-0.2em',
    fontSize: 22,
  },
  title: {
    color: '#fff',
  },
  cooling: {
    color: colors.blue,
  },
  heating: {
    color: colors.red,
  },
  online: {
    color: colors.green,
  },
  menuOptions: {
    padding: '0.7em',
  },
  tempGauge: {
    borderColor: '#fff',
    borderLeftStyle: 'solid',
  },
};

SysStatusOption.propTypes = {
  classes: PropTypes.object, // styling
  togglePower: PropTypes.func.isRequired, // on mains update
  ambient: PropTypes.number.isRequired, // room temp
  ambientRising: PropTypes.bool.isRequired, // is room temp going up?
  mainsStatus: PropTypes.bool.isRequired, // mains power source status
  flash: PropTypes.bool.isRequired, // indicates if temp arrow should be flashing
};

export default withStyles(styles)(SysStatusOption);
