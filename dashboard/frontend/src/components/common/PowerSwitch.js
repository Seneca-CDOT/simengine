import React from 'react';
import PropTypes from 'prop-types';
import { FormControlLabel, Switch } from '@material-ui/core';
import { withStyles } from '@material-ui/core/styles';

import colors from '../../styles/colors';

function PowerSwitch({ onChange, checked, label, classes }) {
  return (
    <FormControlLabel
      control={
        <Switch
          checked={checked}
          onChange={onChange}
          classes={{
            switchBase: classes.colorSwitchBase,
            checked: classes.colorChecked,
            bar: classes.colorBar,
          }}
          aria-label="PowerSwitch"
        />
      }
      label={label}
    />
  );
}

const styles = {
  colorSwitchBase: {
    color: colors.red,
    '&$colorChecked': {
      color: colors.green,
      '& + $colorBar': {
        backgroundColor: colors.green,
      },
    },
  },
  colorBar: {},
  colorChecked: {},
};

PowerSwitch.propTypes = {
  classes: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  checked: PropTypes.bool.isRequired,
  label: PropTypes.object.isRequired,
};

export default withStyles(styles)(PowerSwitch);
