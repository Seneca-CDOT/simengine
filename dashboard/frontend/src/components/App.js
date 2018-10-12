/* eslint-disable */
import React, { Component } from 'react';
import { Stage, Layer, Line } from 'react-konva';
import gridBackground from '../images/grid.png';
import PropTypes from 'prop-types';

// Material
import { withStyles } from '@material-ui/core/styles';
import Snackbar from '@material-ui/core/Snackbar';

// Local Components - Layout
import Pdu from './Assets/PDU/Pdu';
import Socket from './Assets/common/Socket';
import Server from './Assets/Server/Server';
import Ups from './Assets/UPS/Ups';

// Text & info boxes
import AssetDetails from './AssetDetails';
import TopNav from './TopNav';

// few helpers
import { onWheelScroll, onWheelDown } from './canvasEvents';
import simengineSocketClient from './socketClient';

import colors from '../styles/colors';


const drawerWidth = 240;

 class App extends Component {

  constructor() {
    super();

    this.state = {
      assets: null,
      selectedAssetKey: 0,
      connections:{},
      ambient: 0,
      ambientRising: false,
      mainsStatus: 1,
      socketOffline: true,
      changesSaved: false,
    };

    // establish client-server connection
    this.connectToSocket();
  }

  componentDidMount() {
    let stage = this.refs.stage.getStage();
    // scale on wheel scroll, and move canvas on middle button click
    onWheelScroll(stage);
    onWheelDown(stage);
  }

  connectToSocket() {

    if (!("WebSocket" in window)) {
      alert("WebSocket is NOT supported by your Browser!");
      return;
    }

    // Establish connection with the simengine web socket
    this.ws = new simengineSocketClient({

      /** 1st time connection -> initialize system topology */
      onTopologyReceived: (data) => {
        let connections = {};
        const { assets } = data;

        Object.keys(assets).map((key) => {

          // set up connections (wirings) between assets if there's a parent
          if (assets[key]['parent']) {
            for (const parent of assets[key]['parent']) {
              const isComponent = !assets[parent.key];

              // get parent x, y values (parent can be a component (e.g. pdu outlet))
              const { x_conn, y_conn } = isComponent
                                ? assets[this._get_parent_key(parent.key)].children[parent.key]
                                : assets[parent.key];

              connections[parent.key] = {
                sourceX: x_conn?x_conn:0,
                sourceY: y_conn?y_conn:0,
                destX: assets[key].x_conn?assets[key].x_conn:0,
                destY: assets[key].y_conn?assets[key].y_conn:0,
                destKey: key
              };
            }
          }
        });

        console.log(connections)
        this.setState({ assets, connections });
      },

      /** asset updates (power, load, battery etc... )  */
      onAssetReceived: (data) => {
        let assets = {...this.state.assets};
        const isComponent = !this.state.assets[data.key];

        if (isComponent) {
          const parentId = this._get_parent_key(data.key);
          let assetDetails = {...assets[parentId].children[data.key]};
          assets[parentId].children[data.key] = {...assetDetails, ...data};
        } else {
          assets[data.key] = {...assets[data.key], ...data};
        }

        this.setState({ assets });
      },

      /** ambient updates */
      onAmbientReceived: (data) => {
        this.setState({ ambient: data.ambient, ambientRising: data.rising });
      },

      /** main power update */
      onMainsReceived: (data) => {
        this.setState({ mainsStatus: data.mains });
      }
    });

    // when websocket is connected
    this.ws.onOpen(() => {
      this.setState({ socketOffline: false });
    });

    // websocket is closed. try to reconnect every 5 seconds
    this.ws.onClose(() => {
        this.setState({ socketOffline: true });
        setTimeout(() => {this.connectToSocket();}, 5000);
    });
  }

  _get_parent_key(key) {
    const strkey = (''+key);
    return strkey.substring(0, strkey.length===1?1:strkey.length-1);
  }

  _get_asset_by_key(key) {
    if (key && !this.state.assets[key]) {
      const parent_key = this._get_parent_key(key);
      return this.state.assets[parent_key].children[key];
    } else {
      return this.state.assets[key];
    }
  }

  _update_wiring(asset, key, coord) {
    let newConn = {};
    const connections = this.state.connections;

    if(asset['parent']) {
      asset['parent'].forEach((p, idx) => {
        console.log(coord)
        newConn[p] = {...connections[p.key], destX:coord[idx].x, destY:coord[idx].y};
      });
      for (const p of asset['parent']) {

        // x+=250;
      }
    } else if (key in connections) {
      console.log(coord[0])
      newConn[key] = { ...connections[key], sourceX:coord[0].x,  sourceY:coord[0].x };
    }

    return newConn;
  }

  /** Update connections between assets (wires) */
  onPosChange(key, coord) {

    const asset = this._get_asset_by_key(key);

    const connections = this.state.connections;
    console.log(coord)
    let newConn = this._update_wiring(asset, key, coord.inputConnections);

    // for (const ckey of Object.keys(coord.inputConnections)) {
    //   let newConn = this._update_wiring(asset, key, coord.x + coord.inputCenterX, coord.y + coord.inputCenterY);
    // }

    let childConn = {};

    let assets = {...this.state.assets};
    let asset_details = {...assets[key]};
    assets[key] = {...asset_details, ...{x: coord.x, y: coord.y }};

    if (asset.children) {
      for (const ckey of Object.keys(coord.outputConnections)) {
        const c = this._update_wiring(
          this._get_asset_by_key(ckey), ckey, [{x: coord.x + coord.outputConnections[ckey].x, y: coord.y + coord.outputConnections[ckey].y}]
        );

        Object.assign(childConn, c);
      }
    }

    this.setState({ assets, connections: {...connections, ...newConn, ...childConn }});
  }

  /** Handle Asset Selection */
  onElementSelection(assetKey, assetInfo) {
    this.setState((oldState) => {
      return {
        selectedAssetKey: oldState.selectedAssetKey === assetKey ? 0 : assetKey,
        selectedAsset: assetInfo
      };
    });
  }

  /** Send a status change request */
  changeStatus(assetKey, assetInfo) {
    let data = {...assetInfo};
    data.status = !data.status;
    this.ws.sendData({ request: 'power', key: assetKey, data });
  }

  /** Save assets' coordinates in db  */
  saveLayout() {
    let data = {};
    const { assets, connections } = this.state;

    const stage = this.refs.stage.getStage();
    const stageLayout = {
      scale: stage.scaleX(),
      x: stage.x(),
      y: stage.y()
    };

    data['stage'] = stageLayout;
    data['assets'] = {};

    Object.keys(assets).forEach((assetId) => {
      if (assets[assetId]['children']) {
         Object.keys(assets[assetId]['children']).forEach((childId) => {
           if (childId in connections) {
              const child = assets[assetId]['children'][childId];
              data['assets'][childId] = {x:0 ,y:0}
           }
         });
      }
    });

    // add asset layout info
    Object.keys(assets).map((a) => ( data['assets'][a]={ x: assets[a].x, y: assets[a].y }));
    Object.keys(connections).map((a) => {

      data['assets'][a].x_conn = connections[a].sourceX
      data['assets'][a].y_conn = connections[a].sourceY

      data['assets'][connections[a].destKey].x_conn = connections[a].destX
      data['assets'][connections[a].destKey].y_conn = connections[a].destY

    });

    if (this.ws.socketOnline()) {
      this.ws.sendData({request: 'layout', data });
      this.setState({ changesSaved: true });
    }
  }


  /** Add Socket to the Layout */
  drawSocket(key, asset) {
    const powered = asset.parent?this._get_asset_by_key(asset.parent[0].key).status:true;
    return (
    <Socket
      onPosChange={this.onPosChange.bind(this)}
      onElementSelection={this.onElementSelection.bind(this)}
      assetId={key}
      key={key}
      asset={asset}
      selectable={true}
      selected={this.state.selectedAssetKey === key}
      draggable={true}
      powered={powered !== 0}
      x={asset.x}
      y={asset.y}
    />);
  }


  /** Add PDU to the Layout */
  drawPdu(key, asset) {
    const powered = asset.parent?this._get_asset_by_key(asset.parent[0].key).status:false;
    return (
    <Pdu
      onPosChange={this.onPosChange.bind(this)}
      onElementSelection={this.onElementSelection.bind(this)}
      assetId={key}
      key={key}
      asset={asset}
      selected={this.state.selectedAssetKey === key}
      nestedComponentSelected={this.state.selectedAssetKey in asset.children}
      powered={powered !== 0}
      x={asset.x}
      y={asset.y}
    />);
  }

  /* Add Server to the layout */
  drawServer(key, asset) {
    let powered = false;
    if (asset.parent) {
      powered = asset.parent.find((x) => this._get_asset_by_key(x.key).status != 0) !== undefined;
    }

    return (
    <Server
      onPosChange={this.onPosChange.bind(this)}
      onElementSelection={this.onElementSelection.bind(this)}
      assetId={key}
      key={key}
      asset={asset}
      selected={this.state.selectedAssetKey === key}
      nestedComponentSelected={this.state.selectedAssetKey in asset.children}
      powered={powered}
      x={asset.x}
      y={asset.y}
    />);
  }

  /* Add Ups to the layout */
  drawUps(key, asset) {
    let powered = false;
    if (asset.parent) {
      powered = asset.parent.find((x) => this._get_asset_by_key(x.key).status != 0) !== undefined;
    }

    return (
    <Ups
      onPosChange={this.onPosChange.bind(this)}
      onElementSelection={this.onElementSelection.bind(this)}
      assetId={key}
      key={key}
      asset={asset}
      selected={this.state.selectedAssetKey === key}
      nestedComponentSelected={this.state.selectedAssetKey in asset.children}
      powered={powered !== 0}
      x={asset.x}
      y={asset.y}
    />);
  }


  render() {

    const { classes } = this.props;
    const { assets, connections } = this.state;

    // currently selected asset
    const selectedAsset = assets ? this._get_asset_by_key(this.state.selectedAssetKey) : null;

    // asset drawings & their connections
    let systemLayout = [];
    let wireDrawing = [];

    if (assets) {
      // Initialize HA system layout
      for (const key of Object.keys(assets)) {
        if (assets[key].type == 'outlet' || assets[key].type === 'staticasset') {
          systemLayout.push(this.drawSocket(key, assets[key]));
        } else if (assets[key].type === 'pdu') {
          systemLayout.push(this.drawPdu(key, assets[key]));
        } else if (assets[key].type === 'server' || assets[key].type === 'serverwithbmc') {
          systemLayout.push(this.drawServer(key, assets[key]));
        } else if (assets[key].type === 'ups') {
          systemLayout.push(this.drawUps(key, assets[key]));
        }
      }

      // draw wires
      for (const key of Object.keys(connections)) {
        const asset = this._get_asset_by_key(key);

        wireDrawing.push(
          <Line
            points={[
              connections[key].sourceX,
              connections[key].sourceY,
              connections[key].destX,
              connections[key].destY
            ]}
            stroke={asset.status===1?colors.green:"grey"}
            strokeWidth={5}
            zIndex={300}
            key={`${key}${connections[key].destKey}`}
          />
        );
      }
    }

    const snackbarOrigin = {vertical: 'bottom', horizontal: 'left',};

    return (
      <div className={classes.root}>
        <div className={classes.appFrame}>

          {/* Top-Navigation component */}
          <TopNav
            saveLayout={this.saveLayout.bind(this)}
            ambient={this.state.ambient}
            ambientRising={this.state.ambientRising}
            mainsStatus={this.state.mainsStatus}
            togglePower={(status) => this.ws.sendData({ request: 'mains', mains: status })}
            classes={classes}
          />

          {/* Main Canvas */}
          <main className={classes.content} style={{ backgroundImage: 'url('+gridBackground+')', backgroundRepeat: "repeat",  backgroundSize: "auto" }}>
            <div className={classes.toolbar} />

            {/* Drawings */}
            <Stage
              width={window.innerWidth}
              height={window.innerHeight * 0.88}
              ref="stage"
            >
              <Layer>
                {systemLayout}
                {wireDrawing}
              </Layer>
            </Stage>

            {/* RightMost Card -> Display Element Details */}
            {(this.state.selectedAssetKey) ?
              <AssetDetails
                assetInfo={selectedAsset}
                assetKey={this.state.selectedAssetKey}
                changeStatus={this.changeStatus.bind(this)}
              /> : ''
            }

            {/* Display message if backend is not available */}
            <Snackbar
              anchorOrigin={snackbarOrigin}
              open={this.state.socketOffline}
              message={<span>Socket is unavailable: trying to reconnect...</span>}
            />

            {/* 'Changes Applied'/'Saved' Message */}
            <Snackbar
              anchorOrigin={snackbarOrigin}
              open={this.state.changesSaved}
              onClose={()=>this.setState({changesSaved: false})}
              autoHideDuration={1500}
              message={<span>Changes saved!</span>}
            />
            {/* The layout was not initialized -> display link to the documentation*/}
            <Snackbar
              anchorOrigin={snackbarOrigin}
              open={!this.state.socketOffline && !assets}
              message={<span>The system toplology appears to be empty. <br/> Please, refer to the documentation
                (System Modelling <a href="https://simengine.readthedocs.io/en/latest/SystemModeling/">link</a>)</span>}
            />
          </main>
        </div>
      </div>
    );
  }
}
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
    marginLeft: drawerWidth,
  },
  drawerPaper: {
    width: drawerWidth
  },
  toolbar: theme.mixins.toolbar,
  content: {
    flexGrow: 1,
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing.unit * 3,
  },
  menuButton: {
    marginLeft: -12,
    marginRight: 20,
  },
  list: {
    width: 250,
  },
});


App.propTypes = {
  classes: PropTypes.object, // stype
};


export default withStyles(styles)(App);
