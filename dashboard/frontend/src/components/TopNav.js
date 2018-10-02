import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

// Material imports
import { withStyles } from '@material-ui/core/styles';
import { Settings, AcUnit, PowerSettingsNew, ArrowDownward } from "@material-ui/icons";
// import s from "@material-ui/icons/ArrowUpward";
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import Grid from '@material-ui/core/Grid';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import { Divider, Drawer, FormControlLabel, Switch } from '@material-ui/core';


class TopNav extends React.Component {

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
      <div >
      <AppBar
        position="absolute"
        className={classNames(classes.appBar, classes[`appBar-left`])}
      >
        <Toolbar>
          <Typography variant="title" color="inherit" noWrap>
            HAos Simulation Engine
          </Typography>
          <div style={styles.grow} >
            <IconButton aria-owns={drawerOpen ? 'menu-appbar' : null}
                aria-haspopup="true"
                color="inherit"
                onClick={this.handleMenu}
            >
            <Settings/>
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
          <div>
          <Grid container>
            <Grid item >
              <FormControlLabel
                control={
                  <Switch 
                    checked={false} 
                   
                    classes={{
                      switchBase: classes.colorSwitchBase,
                      checked: classes.colorChecked,
                      bar: classes.colorBar,
                    }}
                    aria-label="PowerSwitch"
                  />
                }
                label={
                  <Typography variant="title" style={{color: 'white'}}>
                    <PowerSettingsNew style={styles.inlineIcon} />
                      The Mains: <span  style={styles.heating}> offline</span>
                  </Typography>
                }
              />
            </Grid> 
            <Grid item style={{...styles.menuOptions, ...styles.tempGauge}}>
              <Typography variant="title" color="inherit" >
              
                <AcUnit style={styles.inlineIcon}/>
             
                <span style={styles.cooling}>21° <ArrowDownward style={styles.inlineIcon}/></span> 
              </Typography>
            </Grid>
          </Grid>
          </div>

        </Toolbar>
      </AppBar>
      </div>
    );
  }
}

const colors = {
  on: '#27ae60',
  off: '#e74c3c',
  cooling: '#3498db',
}

const styles = {
  root: {
    flexGrow: 1,
  },
  inlineIcon: {
    marginRight: '0.3em',
    marginBottom: '-0.2em',
    fontSize: 22
  },
  grow: {
    flexGrow: 1,
  },
  colorSwitchBase: {
    color: colors.off,
    '&$colorChecked': {
      color: colors.on,
      '& + $colorBar': {
        backgroundColor: colors.on,
      },
    },
  },
  colorBar: {},
  colorChecked: {},
  cooling: {
    color: colors.cooling
  },
  heating: {
    color: colors.off
  },
  online: {
    color: colors.on
  },
  rightMenuContainer: {
    display: 'flex',
    direction: 'column'
  },
  menuOptions: {
    padding: '0.7em',
  },
  tempGauge: {
    borderColor:"white", 
    borderRightStyle: 'solid',
    borderLeftStyle: 'solid',
  }
};

TopNav.propTypes = {
  classes: PropTypes.object, // styling
  saveLayout: PropTypes.func.isRequired // drawer Save Layout callback
};


export default  withStyles(styles)(TopNav);
