import React, { Component } from 'react';
import { Stage, Layer } from 'react-konva';
import gridBackground from '../images/grid2.png';

import Drawer from '@material-ui/core/Drawer';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Divider from '@material-ui/core/Divider';
import classNames from 'classnames';
import Pdu from './Assets/PDU/Pdu';
import Socket from './Assets/common/Socket';
import SimpleCard from './SimpleCard';


const elementInfo = {
  '1111' : {
    'status': 'off',
    'type': 'PDU',
    'children': [
      '11111',
      '11112',
      '11113',
      '11114'
    ]
  },
  '1112' : {
    'status': 'off',
    'type': 'Socket'
  },
  '11111' : {
    'status': 'off',
    'type': 'Socket'
  },
  '11112' : {
    'status': 'off',
    'type': 'Socket'
  },
  '11113' : {
    'status': 'off',
    'type': 'Socket'
  },
  '11114' : {
    'status': 'off',
    'type': 'Socket'
  },
  '11115' : {
    'status': 'off',
    'type': 'Socket'
  },
  '11116' : {
    'status': 'off',
    'type': 'Socket'
  },
  '11117' : {
    'status': 'off',
    'type': 'Socket'
  },
  '11118' : {
    'status': 'off',
    'type': 'Socket'
  }
}

const drawerWidth = 350;
const styles = theme => ({
  root: {
    flexGrow: 1,
  },
  appFrame: {

    zIndex: 1,
    overflow: 'hidden',
    position: 'relative',
    display: 'flex',
    width: '100%',
  },
  appBar: {
    width: `calc(100% - ${drawerWidth}px)`,
  },
  'appBar-left': {
    marginLeft: drawerWidth,
  },
  'appBar-right': {
    marginRight: drawerWidth,
  },
  drawerPaper: {
    position: 'relative',
    width: drawerWidth,
  },
  toolbar: theme.mixins.toolbar,
  content: {
    flexGrow: 1,
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing.unit * 3,
  },
});

 class App extends Component {

  state = {
    selectedElement: null
  }

  onPosChange(s) {
    console.log(s.target.attrs.x);
    console.log(s.target.attrs.y);
  }

  onElementSelection(elementId) {
    this.setState({
      selectedElement: String(elementId)
    });
  }

  render() {

    const { classes } = this.props;

    return (
      <div className={classes.root}>
        <div className={classes.appFrame}>
          <AppBar
            position="absolute"
            className={classNames(classes.appBar, classes[`appBar-left`])}
          >
            <Toolbar>
              <Typography variant="title" color="inherit" noWrap>
                HA Simulation Engine
              </Typography>
            </Toolbar>
          </AppBar>
          <Drawer
            variant="permanent"
            anchor="right"
            classes={{
              paper: classes.drawerPaper,
            }}
          >
            <div className={classes.toolbar} />
            <Divider />
            <div style={ {margin: 20} }>
            {this.state.selectedElement &&
              <SimpleCard elementInfo={elementInfo} assetId={this.state.selectedElement}/>
            }

            </div>

          </Drawer>

          <main className={classes.content} style={ { backgroundImage: 'url('+gridBackground+')', backgroundRepeat: "repeat" }}>

            <div className={classes.toolbar} />
            <Stage width={window.innerWidth} height={1000}>
              <Layer>
                <Socket
                  onPosChange={this.onPosChange}
                  onElementSelection={this.onElementSelection.bind(this)}
                  elementId={1112}
                  selectable={true}
                  x={10}
                  y={10}
                />
                <Pdu
                  onPosChange={this.onPosChange}
                  onElementSelection={this.onElementSelection.bind(this)}
                  elementId={1111}
                />
              </Layer>
            </Stage>
          </main>
        </div>
      </div>
    );
  }
}

export default  withStyles(styles)(App);
