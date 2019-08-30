import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography,
} from '@material-ui/core';

// ** local imports
import PowerSwitch from './common/PowerSwitch';
import colors from '../styles/colors';

const AssetDetails = ({ classes, asset, changeStatus }) => {
  let children = [];
  const assetStateSpan = {
    1: <span className={classes.statusOn}>on</span>,
    0: <span className={classes.statusOff}>off</span>,
  };

  if (asset.children) {
    children.push(
      <div key={0}>
        <h3> Connected Components </h3>
      </div>,
    );

    const c = asset.children;
    for (const ckey of Object.keys(c)) {
      children.push(
        <div key={ckey}>
          <Typography variant="subheading" component="h5">
            {ckey}-{c[ckey].type} is {assetStateSpan[c[ckey].status]}
          </Typography>
        </div>,
      );
    }
  }

  return (
    <div>
      <Card className={classes.card}>
        <CardHeader
          title="Selected Asset Details"
          className={classes.cardHeader}
        />
        <CardContent>
          <Typography variant="headline" component="h2">
            Asset: {asset.key}-{asset.type}
          </Typography>
          <Typography variant="subheading" component="h5">
            Status: {assetStateSpan[asset.status]}
          </Typography>
          <Typography variant="subheading" component="h5">
            Name: {asset.name}
          </Typography>

          <Typography variant="subheading" component="h5">
            Current Load: {asset.load ? asset.load.toFixed(2) : 0} Amp
          </Typography>
          <Divider />
          {/* Turn off/on the component */}
          <PowerSwitch
            checked={asset.status === 1}
            onChange={() => changeStatus(asset)}
            label={
              <Typography variant="subheading" component="h5">
                Toggle Status
              </Typography>
            }
          />
          <Divider />
          {/* Display any nested elements */}
          <div className={classes.nestedElements}>{children}</div>
        </CardContent>
      </Card>
    </div>
  );
};

AssetDetails.propTypes = {
  classes: PropTypes.object.isRequired,
  asset: PropTypes.object.isRequired,
  changeStatus: PropTypes.func.isRequired, // Change asset state
};

const styles = {
  card: {
    minWidth: 320,
    position: 'absolute',
    top: 90,
    right: 20,
  },
  nestedElements: {
    maxHeight: 500,
    overflow: 'auto',
  },
  cardHeader: {
    backgroundColor: '#e1e6ea',
  },
  statusOn: {
    color: colors.greenDark,
  },
  statusOff: {
    colors: colors.grey,
  },
  bullet: {
    display: 'inline-block',
    margin: '0 2px',
    transform: 'scale(0.8)',
  },
  title: {
    marginBottom: 16,
    fontSize: 14,
  },
  pos: {
    marginBottom: 12,
  },
};

export default withStyles(styles)(AssetDetails);
