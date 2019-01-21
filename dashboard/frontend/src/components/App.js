import React, { Component } from 'react';
import { Stage } from 'react-konva';
import gridBackground from '../images/grid.png';
import PropTypes from 'prop-types';

// Material
import { withStyles } from '@material-ui/core/styles';
import Snackbar from '@material-ui/core/Snackbar';

// Local Components - Layout

// Text & info boxes
import AssetDetails from './AssetDetails';
import TopNav from './Navigation/TopNav';
import Canvas from './Canvas';

// few helpers
import { onWheelScroll, onWheelDown } from './canvasEvents';
import simengineSocketClient from './socketClient';



const drawerWidth = 240;

class App extends Component {

  constructor() {
    super();

    this.state = {
      assets: null,
      selectedAssetKey: 0,
      connections: {},
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
        const { assets, stageLayout } = data;

        Object.keys(assets).map((key) => {
          if (assets[key]['parent']) {
            for (const parent of assets[key]['parent']) {
              connections[parent.key] = {
                sourceX: 0, sourceY: 0,
                destX:   0, destY: 0,
                destKey: key
              };
            }
          }
        });

        if (stageLayout) {
          let stage = this.refs.stage.getStage();
          stage.position({ x: stageLayout.x, y: stageLayout.y });
          stage.scale({ x: stageLayout.scale, y: stageLayout.scale });
        }

        this.setState({ assets, connections });
      },

      /** asset updates (power, load, battery etc... )  */
      onAssetReceived: (data) => {
        let assets = {...this.state.assets};
        const isComponent = !this.state.assets[data.key];

        if (isComponent) {
          const parentId = this._getParentKey(data.key);
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

  _getParentKey(key) {
    const strkey = (''+key);
    return strkey.substring(0, strkey.length===1?1:strkey.length-1);
  }

  _updateWiring(asset, key, coord) {

    let newConn = {};
    const connections = this.state.connections;

    if(asset['parent']) {
      asset['parent'].forEach((p, idx) => {
        newConn[p.key] = {...connections[p.key], destX:coord[idx].x, destY:coord[idx].y };
      });
    } else if (key in connections && coord[0]) {
      newConn[key] = { ...connections[key], sourceX:coord[0].x, sourceY:coord[0].y };
    }

    return newConn;
  }

  getAssetByKey(key) {
    if (key && !this.state.assets[key]) {
      const parentKey = this._getParentKey(key);
      return this.state.assets[parentKey].children[key];
    } else {
      return this.state.assets[key];
    }
  }


  /** Update connections between assets (wires) */
  onPosChange(key, coord) {

    const asset = this.getAssetByKey(key);

    // find all the incoming connections as well as output wiring
    const connections = this.state.connections;
    let newConn = this._updateWiring(asset, key, coord.inputConnections.map((c)=>c={x: c.x+coord.x, y: c.y+coord.y}));
    let childConn = {};

    let assets = {...this.state.assets};
    if (assets[key]) {
      let assetDetails = {...assets[key]};
      assets[key] = {...assetDetails, ...{x: coord.x, y: coord.y }};
    }

    // output wiring
    if (asset.children) {
      for (const ckey of Object.keys(coord.outputConnections)) {
        const c = this._updateWiring(
          this.getAssetByKey(ckey), ckey, [{x: coord.x + coord.outputConnections[ckey].x, y: coord.y + coord.outputConnections[ckey].y}]
        );

        Object.assign(childConn, c);
      }
    }

    this.setState({ assets, connections: {...connections, ...newConn, ...childConn }});
  }

  /** Handle Asset Selection (deselect on second click, select asset otherwise) */
  onElementSelection(asset) {
    this.setState((oldState) => {
      return {
        selectedAssetKey: oldState.selectedAssetKey === asset.key ? 0 : asset.key,
        selectedAsset: asset
      };
    });
  }

  /** Send a status change request */
  changeStatus(asset) {
    let data = {...asset};
    data.status = !data.status;
    this.ws.sendData({ request: 'power', key: asset.key, data });
  }

  /** Save assets' coordinates in db  */
  saveLayout() {
    let data = {};
    const { assets } = this.state;

    const stage = this.refs.stage.getStage();
    const stageLayout = {
      scale: stage.scaleX(),
      x: stage.x(),
      y: stage.y()
    };

    data['stage'] = stageLayout;
    data['assets'] = {};

    // add asset layout info
    Object.keys(assets).map((a) => ( data['assets'][a]={ x: assets[a].x, y: assets[a].y }));

    if (this.ws.socketOnline()) {
      this.ws.sendData({request: 'layout', data });
      this.setState({ changesSaved: true });
    }
  }


  render() {

    const { classes } = this.props;
    const { assets, connections } = this.state;

    // currently selected asset
    const selectedAsset = assets ? this.getAssetByKey(this.state.selectedAssetKey) : null;

    const snackbarOrigin = {vertical: 'bottom', horizontal: 'left',};

    return (
      <div className={classes.root}>
        <div className={classes.appFrame}>

          {/* Top-Navigation component */}
          <TopNav
            saveLayout={this.saveLayout.bind(this)}
            ambient={this.state.ambient}
            ambientRising={this.state.ambientRising}
            mainsStatus={!!this.state.mainsStatus}
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
              <Canvas
                getAssetByKey={this.getAssetByKey.bind(this)}
                onPosChange={this.onPosChange.bind(this)}
                onElementSelection={this.onElementSelection.bind(this)}
                assets={assets}
                connections={connections}
                selectedAssetKey={this.state.selectedAssetKey}
              />
            </Stage>

            {/* RightMost Card -> Display Element Details */}
            {(this.state.selectedAssetKey) ?
              <AssetDetails
                asset={selectedAsset}
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
              message={
                <span>
                  The system toplology appears to be empty. <br/>
                  Please, refer to the documentation (System Modelling
                  <a href="https://simengine.readthedocs.io/en/latest/SystemModeling/">link</a>)
                </span>
              }
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
