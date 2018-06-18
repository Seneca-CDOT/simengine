/* eslint-disable */
import React, { Component } from 'react';
import { Stage, Layer, Shape, Line } from 'react-konva';
import Konva from 'konva';
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
      layoutScaleX: 1,
      layoutScaleY: 1,
      startSocketX: 63,
      startSocketY: 38
    }
    var stage = new Konva.stage({
       width:window.innerWidth,
       height:1100,
    });

    var layer = new Konva.Layer();
    stage.add(layer);

    window.addEventListener('wheel', (e) => {
      e.preventDefault();
      var oldScale = stage.scaleX();

      var mousePointTo = {
          x: stage.getPointerPosition().x / oldScale - stage.x() / oldScale,
          y: stage.getPointerPosition().y / oldScale - stage.y() / oldScale,
      };

      var newScale = e.deltaY > 0 ? oldScale * scaleBy : oldScale / scaleBy;
      stage.scale({ x: newScale, y: newScale });

      var newPos = {
          x: -(mousePointTo.x - stage.getPointerPosition().x / newScale) * newScale,
          y: -(mousePointTo.y - stage.getPointerPosition().y / newScale) * newScale
      };
      stage.position(newPos);
      stage.batchDraw();
  }).bind(this);
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

              let childInfo = eInfo[data.key].children;
              eInfo[data.key] = data.data;
              eInfo[data.key].children = childInfo;
              // console.log(eInfo)

              this.setState({
                assets: eInfo
              });
            }

          } else {
            this.setState({
              assets: data
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

  _get_asset_by_key(key) {
    if ((''+key).length === 5) {
      const parent_key = (''+key).substring(0, 4);
      console.log("key: " + key)
      return this.state.assets[parent_key].children[key];
    } else {
      return this.state.assets[key];
    }
  }



  onPosChange(key, s) {
    console.log("POS CHANGED OF " + key)
    console.log(s.target.attrs.x);
    console.log(s.target.attrs.y);
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
      onPosChange={this.onPosChange}
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
      onPosChange={this.onPosChange}
      onElementSelection={this.onElementSelection.bind(this)}
      assetId={key}
      asset={asset}
      selected={this.state.selectedAssetKey === key}
      pduSocketSelected={this.state.selectedAssetKey in asset.children}
    />);
  }

  _drawWire(context) {

    //console.log(state)
    let width = 100,
    height = 500;

let pts = { st: [3, 38],
  ct: [width, height/4, width, 3/4*height],
  en: [width/2, 3/4*height]
}
    context.beginPath();
    context.moveTo(...pts.st);
    context.bezierCurveTo(...pts.ct,...pts.en);
    context.strokeShape(this);
  }



  render() {

    const { classes } = this.props;
    const assets = this.state.assets;

    const selectedAsset = this._get_asset_by_key(this.state.selectedAssetKey)
    let systemLayout = [];
    let connections=[]

    // Initialize HA system layout
    for (const key of Object.keys(assets)) {
      if (assets[key].type == 'outlet') {
        systemLayout.push(this.drawSocket(key, assets[key]))
      } else if (assets[key].type == 'pdu') {
        systemLayout.push(this.drawPdu(key, assets[key]))
      }
    }

    connections.push(<Line
      x={this.state.startSocketX}
      y={this.state.startSocketY}
      points={[10, 10, 50, 50, 100, 100]}
      fill={'green'}
      closed={true}


      />)

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
            {this.stage}
            {/*
            <Stage width={window.innerWidth} height={1100} scale={{x: this.state.layoutScaleX, y: this.state.layoutScaleY}}>
              <Layer>
                {systemLayout}
                {connections}
                {
                <Shape

                  strokeWidth={4}
                  stroke={'grey'}
                  lineCap={'round'}
                  sceneFunc={this._drawWire}
                /> }
              </Layer>
            </Stage>
            */}
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
