import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

import { Settings } from '@material-ui/icons';
import {
  IconButton,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemText,
} from '@material-ui/core';
import { withStyles } from '@material-ui/core/styles';

/**
 * Drawer option/settings
 */
class SettingsOption extends React.Component {
  constructor(props) {
    super(props);
    this.state = { drawerAnchor: null };
  }

  openDrawer = event => this.setState({ drawerAnchor: event.currentTarget });
  handleDrawerClose = () => this.setState({ drawerAnchor: null });

  render() {
    const { classes, plays, executePlay, saveLayout } = this.props;

    const { drawerAnchor } = this.state;
    const drawerOpen = Boolean(drawerAnchor);

    let playList = [];
    for (const playName of plays) {
      playList.push(
        <ListItem button key={playName} onClick={() => executePlay(playName)}>
          <ListItemText primary={playName} />
        </ListItem>,
      );
    }

    return (
      <Fragment>
        {/* Button to open up a menu */}
        <IconButton
          aria-owns={drawerOpen ? 'menu-appbar' : null}
          aria-haspopup="true"
          color="inherit"
          onClick={this.openDrawer}
        >
          <Settings />
        </IconButton>

        {/* Sidebar menu */}
        <Drawer
          open={drawerOpen}
          onClose={this.handleDrawerClose}
          classes={{ paper: classes.drawerPaper }}
          anchor={'left'}
        >
          <div className={classes.toolbar} />
          <Divider />
          <div
            tabIndex={0}
            role="button"
            onClick={this.handleDrawerClose}
            onKeyDown={this.handleDrawerClose}
            className={classes.fullList}
          >
            {/* Sidebar options */}
            <List>
              <ListItem button onClick={saveLayout}>
                <ListItemText primary="Save Layout" />
              </ListItem>
              <ListItem
                button
                onClick={() =>
                  window.open('https://simengine.readthedocs.io/en/latest/')
                }
              >
                <ListItemText primary="View Documentation" />
              </ListItem>
              {!!plays.length && (
                <ListItem key={'title'}>
                  <h3>Scenarios</h3>
                </ListItem>
              )}
              {playList}
            </List>
          </div>
        </Drawer>
      </Fragment>
    );
  }
}

const styles = theme => ({
  toolbar: theme.mixins.toolbar,
  drawerPaper: {
    width: 240,
  },
});

SettingsOption.propTypes = {
  classes: PropTypes.object, // styling
  saveLayout: PropTypes.func.isRequired, // drawer Save Layout callback
  plays: PropTypes.array,
  executePlay: PropTypes.func.isRequired,
};

export default withStyles(styles)(SettingsOption);
