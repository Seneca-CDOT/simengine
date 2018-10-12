import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

// Material imports
import { withStyles } from '@material-ui/core/styles';
import { Settings, AcUnit, PowerSettingsNew, ArrowDownward, ArrowUpward } from "@material-ui/icons";
// import s from "@material-ui/icons/ArrowUpward";
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import Grid from '@material-ui/core/Grid';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import { Divider, Drawer, Fade } from '@material-ui/core';

// local imports
import colors from '../styles/colors';
import PowerSwitch from './common/PowerSwitch';


class TopNav extends React.Component {

  constructor(props) {
    super(props);

    this.state = {
      drawerAnchor: null,
      ambientRising: false,
      lastTempChange: new Date(),
      flash: false,
    };

    this.flashArrow = null;
  }

  componentWillReceiveProps(newProps) {

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
              <PowerSwitch
                checked={this.props.mainsStatus}
                onChange={()=>this.props.togglePower(!this.props.mainsStatus)}
                label={
                  <Typography variant="title" style={{color: 'white'}}>
                    <PowerSettingsNew style={styles.inlineIcon} />
                      The Mains:
                      <span  style={this.props.mainsStatus?styles.online:styles.heating}>
                        {" "}{this.props.mainsStatus?"online":"offline"}
                      </span>
                  </Typography>
                }
              />
            </Grid>
            <Grid item style={{...styles.menuOptions, ...styles.tempGauge}}>
              <Typography variant="title" color="inherit" >
                <AcUnit style={styles.inlineIcon}/>
                <span style={(this.props.ambient>27)?styles.heating:styles.cooling}>{this.props.ambient}°
                  <Fade in={this.state.flash}>
                    {this.state.ambientRising
                      ? <ArrowUpward style={styles.inlineIcon}/>
                      : <ArrowDownward style={styles.inlineIcon}/>
                    }
                  </Fade>
                </span>
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
  cooling: {
    color: colors.blue
  },
  heating: {
    color: colors.red
  },
  online: {
    color: colors.green
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
    borderLeftStyle: 'solid',
  }
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
