import React from 'react';
import classNames from 'classnames';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import SettingsIcon from "@material-ui/icons/Settings";
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import {Divider, Drawer} from '@material-ui/core';

export default class TopNav extends React.Component {

  constructor(props) {
    super(props);

    this.state = {
      drawerAnchor: null
    };
  }

  handleMenu = event => {
    this.setState({ drawerAnchor: event.currentTarget });
  };

  handleDrawerClose = () => {
    this.setState({ drawerAnchor: null });
  };

  render() {

    const { classes } = this.props;

    const { drawerAnchor } = this.state;
    const drawerOpen = Boolean(drawerAnchor);

    return (
      <AppBar
        position="absolute"
        className={classNames(classes.appBar, classes[`appBar-left`])}
      >
        <Toolbar>
          <Typography variant="title" color="inherit" noWrap>
            HAos Simulation Engine
          </Typography>
          <div>
            <IconButton aria-owns={drawerOpen ? 'menu-appbar' : null}
                aria-haspopup="true"
                color="inherit"
                onClick={this.handleMenu}
            >
            <SettingsIcon/>
            </IconButton>
              <Drawer open={drawerOpen} onClose={this.handleDrawerClose}
                classes={{paper: classes.drawerPaper,}} anchor={'left'}>
                <div className={classes.toolbar}/>
                <Divider />
                <div
                  tabIndex={0}
                  role="button"
                  onClick={this.handleDrawerClose}
                  onKeyDown={this.handleDrawerClose}
                >
                  <div className={classes.fullList}>
                    <List>
                      <ListItem button onClick={this.props.saveLayout.bind(this)}>
                        <ListItemText primary="Save Layout" />
                      </ListItem>
                    </List>
                  </div>
                </div>
            </Drawer>
          </div>
        </Toolbar>
      </AppBar>
    );
  }

}
