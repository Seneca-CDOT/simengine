/* eslint-disable */
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
import initialState from './InitialState';




const drawerWidth = 0;
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
    backgroundColor: "#36454F",
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

  constructor() {
    super();
    this.state = {
      selectedElement: null,
      elementInfo: initialState
    }
    if ("WebSocket" in window)
    {
       console.log("WebSocket is supported by your Browser!");
       // Let us open a web socket
       this.ws = new WebSocket("ws://localhost:8000/simengine");
       this.ws.onopen = function()
       {
          // Web Socket is connected, send data using send()
          // this.ws.send("Hello server");
          // alert("Message is sent...");
       };
       this.ws.onmessage = ((evt) =>
       {
          var received_msg = evt.data;
          const data = JSON.parse(evt.data);
          // console.log("Message is received:\n" + evt.data);
          if('key' in data){
            // update state
            let eInfo = this.state.elementInfo;

            let childInfo = eInfo[data.key].children
            eInfo[data.key] = data.data;
            eInfo[data.key].children = childInfo;
            // console.log(eInfo)

            this.setState({
              elementInfo: eInfo
            });
          } else {

            this.setState({
              elementInfo: data
            });
          }

       }).bind(this)
       this.ws.onclose = function()
       {
          // websocket is closed.
          alert("Connection is closed...");
       };
    }
    else
    {
       // The browser doesn't support WebSocket
       alert("WebSocket NOT supported by your Browser!");
    }
  }



  onPosChange(s) {
    console.log(s.target.attrs.x);
    console.log(s.target.attrs.y);
  }

  onElementSelection(elementId) {
    this.setState({
      selectedElement: elementId,
    });
  }

  changeStatus(assetId) {
    let data = {...this.state.elementInfo[assetId]};
    data.status = !data.status;
    this.ws.send(JSON.stringify({key: assetId, data }));
  }

  render() {

    const { classes } = this.props;
    const elementInfo = this.state.elementInfo;

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


          <main className={classes.content} style={ { backgroundImage: 'url('+gridBackground+')', backgroundRepeat: "repeat" }}>
          <div style={ {margin: 20} } style={{ maxWidth: 400 }}>
            </div>
            <div className={classes.toolbar} />
            <Stage width={window.innerWidth} height={1100}>
              <Layer>
                <Socket
                  onPosChange={this.onPosChange}
                  onElementSelection={this.onElementSelection.bind(this)}
                  elementId={1112}
                  elementInfo={elementInfo}
                  selectable={true}
                  selectedSocket={this.state.selectedElement}
                  x={10}
                  y={10}
                />
                <Pdu
                  onPosChange={this.onPosChange}
                  onElementSelection={this.onElementSelection.bind(this)}
                  elementId={1111}
                  elementInfo={elementInfo}
                  selectedPdu={this.state.selectedElement}
                />
              </Layer>
            </Stage>
            {/* Display Element Details */}
            {this.state.selectedElement &&
              <SimpleCard elementInfo={elementInfo} assetId={this.state.selectedElement} changeStatus={this.changeStatus.bind(this)}/>
            }
          }
          </main>
        </div>
      </div>
    );
  }
}

export default  withStyles(styles)(App);
