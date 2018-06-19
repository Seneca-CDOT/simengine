import React, { Component } from 'react';
import { Stage, Layer, Line } from 'react-konva';
import gridBackground from '../images/grid.png';

import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import classNames from 'classnames';
import Pdu from './Assets/PDU/Pdu';
import Socket from './Assets/common/Socket';
import SimpleCard from './SimpleCard';
import initialState from './InitialState';


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
    width: `100%`,
  },
  'appBar-left': {
    backgroundColor: "#36454F",
  },
  drawerPaper: {
    position: 'relative',
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
      assets: initialState,
      selectedAssetKey: 0,
      connections:{},
    };

    // this._drawWire = this._drawWire.bind(this)


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
          const data = JSON.parse(evt.data);
          // console.log("Message is received:\n" + evt.data);
          if('key' in data) {
            // nested asset
            if ((''+data.key).length === 5) {
              const parent_id = (''+data.key).substring(0, 4)
              let assets = {...this.state.assets};
              assets[parent_id].children[data.key] = data.data;
              this.setState({ assets });
            } else {
              // update state
              let eInfo = this.state.assets;

              let { children, parent } = eInfo[data.key];
              eInfo[data.key] = data.data;
              eInfo[data.key].children = children;
              eInfo[data.key].parent = parent;

              this.setState({
                assets: eInfo
              });
            }

          } else {
            let connections = {}

            Object.keys(data).map((k) => {
              if (data[k]['parent']) {
                connections[data[k]['parent'].key] = {x: 40, y:0, x1:50, y1:50 }
              }
            });

            this.setState({
              assets: data,
              connections
            });
          }

       }).bind(this);
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

  componentDidMount() {

    // Scale Layout on wheel event
    let stage = this.refs.stage.getStage()
    const scaleBy = 1.03;
    window.addEventListener('wheel', (e) => {
      e.preventDefault();

      const oldScale = stage.scaleX();

      const mousePointTo = {
          x: stage.getPointerPosition().x / oldScale - stage.x() / oldScale,
          y: stage.getPointerPosition().y / oldScale - stage.y() / oldScale,
      };

      const newScale = e.deltaY > 0 ? oldScale * scaleBy : oldScale / scaleBy;
      stage.scale({ x: newScale, y: newScale });

      const newPos = {
          x: -(mousePointTo.x - stage.getPointerPosition().x / newScale) * newScale,
          y: -(mousePointTo.y - stage.getPointerPosition().y / newScale) * newScale
      };
      stage.position(newPos);
      stage.batchDraw();
    });
  }

  _get_asset_by_key(key) {
    if ((''+key).length === 5) {
      const parent_key = (''+key).substring(0, 4);
      return this.state.assets[parent_key].children[key];
    } else {
      return this.state.assets[key];
    }
  }

_update_wiring(asset, key, x, y) {
  let newConn = {};
  const connections = this.state.connections;

  if(asset['parent']) {
    newConn[asset['parent'].key] = { ...connections[asset['parent'].key], x1:x,  y1:y };
  } else if (key in connections) {
    newConn[key] = { ...connections[key], x:x,  y:y };
  }

  return newConn;
}

/** Update connections between assets (wires) */
  onPosChange(key, e) {

    const asset = this._get_asset_by_key(key);
    const connections = this.state.connections;
    let newConn = this._update_wiring(asset, key, e.target.x(), e.target.y());

    let childConn = {};

    let x=100;
    if (asset.children) {
      for (const ckey of Object.keys(asset.children)) {
        const c = this._update_wiring(this._get_asset_by_key(ckey), ckey, e.target.x()+x, e.target.y());
        Object.assign(childConn, c);
        x += 90;
      }
    }

    this.setState({ connections: {...connections, ...newConn, ...childConn }});
  }

  /** Handle Asset Selection */
  onElementSelection(assetKey, assetInfo) {
    this.setState((oldState) => {
      return {
        selectedAssetKey: oldState.selectedAssetKey === assetKey ? 0 : assetKey,
        selectedAsset: assetInfo
      }
    });
  }

  /** Send a status change request */
  changeStatus(assetKey, assetInfo) {
    let data = {...assetInfo};
    data.status = !data.status;
    this.ws.send(JSON.stringify({key: assetKey, data }));
  }


  /** Add Socket to the Layout */
  drawSocket(key, asset) {
    return (
    <Socket
      onPosChange={this.onPosChange.bind(this)}
      onElementSelection={this.onElementSelection.bind(this)}
      assetId={key}
      asset={asset}
      selectable={true}
      selected={this.state.selectedAssetKey === key}
      draggable={true}
    />);
  }


  /** Add PDU to the Layout */
  drawPdu(key, asset) {

    return (
    <Pdu
      onPosChange={this.onPosChange.bind(this)}
      onElementSelection={this.onElementSelection.bind(this)}
      assetId={key}
      asset={asset}
      selected={this.state.selectedAssetKey === key}
      pduSocketSelected={this.state.selectedAssetKey in asset.children}
    />);
  }

  render() {

    const { classes } = this.props;
    const { assets, connections } = this.state;

    const selectedAsset = this._get_asset_by_key(this.state.selectedAssetKey)
    let systemLayout = [];
    let wireDrawing=[];

    // Initialize HA system layout
    for (const key of Object.keys(assets)) {
      if (assets[key].type == 'outlet') {
        systemLayout.push(this.drawSocket(key, assets[key]));
      } else if (assets[key].type == 'pdu') {
        systemLayout.push(this.drawPdu(key, assets[key]));
      }
    }

    // draw wires
    const socketXpad = 34;
    const socketYpad = 35;
    for (const key of Object.keys(connections)) {
      const asset = this._get_asset_by_key(key);
      wireDrawing.push(
        <Line
          points={[connections[key].x+socketXpad, connections[key].y+socketYpad, connections[key].x1-socketXpad, connections[key].y1+socketYpad]}
          stroke={asset.status  === 1?"green":"red"}
          strokeWidth={5}
        />
      );
    }


    return (
      <div className={classes.root}>
        <div className={classes.appFrame}>
          {/* Top-bar */}
          <AppBar
            position="absolute"
            className={classNames(classes.appBar, classes[`appBar-left`])}
          >
            <Toolbar>
              <Typography variant="title" color="inherit" noWrap>
                HAos Simulation Engine
              </Typography>
            </Toolbar>
          </AppBar>

          {/* Main Canvas */}
          <main className={classes.content} style={ { backgroundImage: 'url('+gridBackground+')', backgroundRepeat: "repeat" }}>
            <div className={classes.toolbar} />
            <Stage
              width={window.innerWidth}
              height={1100}
              ref="stage"
            >
              <Layer>
                {systemLayout}
                {wireDrawing}
              </Layer>
            </Stage>
            {/* LeftMost Card -> Display Element Details */}
            {(this.state.selectedAssetKey) ?
              <SimpleCard
                assetInfo={selectedAsset}
                assetKey={this.state.selectedAssetKey}
                changeStatus={this.changeStatus.bind(this)}
              /> : ''
            }
          </main>
        </div>
      </div>
    );
  }
}

export default withStyles(styles)(App);
