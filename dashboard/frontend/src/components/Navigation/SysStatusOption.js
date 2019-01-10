import React from 'react';
import PropTypes from 'prop-types';

import { AcUnit, PowerSettingsNew, ArrowDownward, ArrowUpward } from "@material-ui/icons";
import { Grid, Typography, Fade } from '@material-ui/core';

// local imports
import PowerSwitch from '../common/PowerSwitch';
import colors from '../../styles/colors';

/**
 * Top-Right Nav options
 */
const SysStatusOption = ({ mainsStatus, ambient, ambientRising, flash, togglePower }) => {
  return (
    <Grid container>

      {/* Wall power status */}
      <Grid item>
        <PowerSwitch
          checked={mainsStatus}
          onChange={()=>togglePower(!mainsStatus)}
          label={
            <Typography variant="title" style={{color: 'white'}}>
              <PowerSettingsNew style={styles.inlineIcon} />
                The Mains:
                <span  style={mainsStatus?styles.online:styles.heating}>
                  {" "}{mainsStatus?"online":"offline"}
                </span>
            </Typography>
          }
        />
      </Grid>

      {/* Ambient Temperature */}
      <Grid item style={{...styles.menuOptions, ...styles.tempGauge}}>
        <Typography variant="title" color="inherit" >
          <AcUnit style={styles.inlineIcon}/>
          <span style={(ambient>27)?styles.heating:styles.cooling}>{ambient}°
            <Fade in={flash}>
              {ambientRising
                ? <ArrowUpward style={styles.inlineIcon}/>
                : <ArrowDownward style={styles.inlineIcon}/>
              }
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
    fontSize: 22
  },
  cooling: {
    color: colors.blue
  },
  heating: {
    color: colors.red
  },
  online: {
    color: colors.green
  },
  menuOptions: {
    padding: '0.7em',
  },
  tempGauge: {
    borderColor:"white",
    borderLeftStyle: 'solid',
  }
};


SysStatusOption.propTypes = {
  classes: PropTypes.object, // styling
  togglePower: PropTypes.func.isRequired, // on mains update
  ambient: PropTypes.number.isRequired, // room temp
  ambientRising: PropTypes.bool.isRequired, // is room temp going up?
  mainsStatus: PropTypes.bool.isRequired, // mains power source status
  flash: PropTypes.bool.isRequired, // indicates if temp arrow should be flashing
};

export default SysStatusOption;
