import React, { Component } from 'react';
import { Stage } from 'react-konva';
import PropTypes from 'prop-types';
import update from 'immutability-helper';

// Material
import { withStyles } from '@material-ui/core/styles';

// Local Components - Layout

// Text & info boxes
import AssetDetails from './AssetDetails';
import TopNav from './Navigation/TopNav';
import Canvas from './Canvas';
import Notifications from './Notifications';
import Progress from './Progress';

// few helpers
import { onWheelScroll, onWheelDown, fitStageIntoParent } from './canvasEvents';
import simengineSocketClient from './socketClient';
import styles from './App.styles';

class App extends Component {
  constructor() {
    super();

    this.state = {
      assets: {},
      selectedAssetKey: 0,
      connections: {},
      ambient: 0,
      ambientRising: false,
      mainsStatus: 1,
      socketOffline: true,
      changesSaved: false,
      loadedConnections: 0,
      plays: [],
    };

    // establish client-server connection
    this.connectToSocket();
  }

  componentDidMount() {
    let stage = this.refs.stage.getStage();
    // scale on wheel scroll, and move canvas on middle button click
    onWheelScroll(stage);
    onWheelDown(stage);
    fitStageIntoParent(stage);
  }

  connectToSocket() {
    if (!('WebSocket' in window)) {
      alert('WebSocket is NOT supported by your Browser!');
      return;
    }

    // Establish connection with the simengine web socket
    this.ws = new simengineSocketClient({
      /** 1st time connection -> initialize system topology */
      onTopologyReceived: data => {
        this.setState({ assets: {}, connections: {}, loadedConnections: 0 });

        let connections = {};
        const { assets, stageLayout } = data;
        if (!assets || Object.keys(assets).length === 0) {
          return;
        }

        Object.keys(assets).map(key => {
          if (assets[key]['parent']) {
            for (const parent of assets[key]['parent']) {
              connections[parent.key] = {
                sourceX: 0,
                sourceY: 0,
                destX: 0,
                destY: 0,
                destKey: key,
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
      onAssetReceived: data => {
        let assets = this.state.assets;
        const isComponent = !this.state.assets[data.key];

        if (isComponent) {
          const parentId = this._getParentKey(data.key);
          assets = update(assets, {
            [parentId]: { children: { [data.key]: { $merge: data } } },
          });
        } else {
          assets = update(assets, { [data.key]: { $merge: data } });
        }

        this.setState({ assets });
      },

      /** ambient updates */
      onAmbientReceived: data => {
        this.setState({ ambient: data.ambient, ambientRising: data.rising });
      },

      /** main power update */
      onMainsReceived: data => {
        this.setState({ mainsStatus: data.mains });
      },

      /** scripts that can be executed */
      onPlaylistReceived: data => {
        this.setState({ plays: data.plays });
      },
    });

    // when websocket is connected
    this.ws.onOpen(() => {
      this.setState({ socketOffline: false });

      this.ws.sendData({ request: 'get_sys_status', payload: {} });
      this.ws.sendData({ request: 'subscribe', payload: {} });
    });

    // websocket is closed. try to reconnect every 5 seconds
    this.ws.onClose(() => {
      this.setState({ socketOffline: true });
      setTimeout(() => {
        this.connectToSocket();
      }, 5000);
    });
  }

  _getParentKey(key) {
    const strkey = '' + key;
    return strkey.substring(0, strkey.length === 1 ? 1 : strkey.length - 1);
  }

  _updateWiring(asset, coord) {
    let newConn = {};
    const connections = this.state.connections;

    if (asset['parent']) {
      asset['parent'].forEach((parent, idx) => {
        newConn[parent['key']] = {
          ...connections[parent['key']],
          destX: coord[idx].x,
          destY: coord[idx].y,
        };
      });
    } else if (asset['key'] in connections && coord[0]) {
      newConn[asset['key']] = {
        ...connections[asset['key']],
        sourceX: coord[0].x,
        sourceY: coord[0].y,
      };
    }

    return newConn;
  }

  getAssetByKey = key => {
    if (key && !this.state.assets[key]) {
      const parentKey = this._getParentKey(key);
      return this.state.assets[parentKey].children[key];
    } else {
      return this.state.assets[key];
    }
  };

  /** Update connections between assets (wires) & asset position */
  onPosChange = (key, coord) => {
    const asset = this.getAssetByKey(key);
    let { connections, assets, loadedConnections } = this.state;

    // find all the incoming connections as well as output wiring
    // (connections are relative to the asset position)

    // input connections
    connections = update(connections, {
      $merge: this._updateWiring(
        asset,
        coord.inputConnections.map(
          c => (c = { x: c.x + coord.x, y: c.y + coord.y }),
        ),
      ),
    });

    // update output wirings
    if (asset.children) {
      for (const ckey of Object.keys(coord.outputConnections)) {
        const outCoord = [
          {
            x: coord.x + coord.outputConnections[ckey].x,
            y: coord.y + coord.outputConnections[ckey].y,
          },
        ];
        connections = update(connections, {
          $merge: this._updateWiring(this.getAssetByKey(ckey), outCoord),
        });
      }
    }

    if (
      loadedConnections < Object.keys(connections).length &&
      asset['parent']
    ) {
      loadedConnections += asset['parent'].length;
    }

    // update asset position
    if (assets[key]) {
      assets = update(assets, {
        [key]: {
          x: { $set: coord.x },
          y: { $set: coord.y },
        },
      });
    }

    this.setState({ assets, connections, loadedConnections });
  };

  /** Handle Asset Selection (deselect on second click, select asset otherwise) */
  onElementSelection = asset => {
    this.setState(oldState => {
      return {
        selectedAssetKey:
          oldState.selectedAssetKey === asset.key ? 0 : asset.key,
        selectedAsset: asset,
      };
    });
  };

  /** Send a status change request */
  changeAssetStatus = asset => {
    let payload = { ...asset };
    payload.status = !payload.status;
    this.ws.sendData({ request: 'set_power', payload });
  };

  changeWallpowerStatus = status =>
    this.ws.sendData({ request: 'set_mains', payload: { mains: status } });

  executePlay = name =>
    this.ws.sendData({ request: 'exec_play', payload: { name } });

  /** Save assets' coordinates in db  */
  saveLayout = () => {
    let payload = {};
    const { assets } = this.state;

    const stage = this.refs.stage.getStage();
    const stageLayout = {
      scale: stage.scaleX(),
      x: stage.x(),
      y: stage.y(),
    };

    payload['stage'] = stageLayout;
    payload['assets'] = {};

    // add asset layout info
    Object.keys(assets).map(
      a => (payload['assets'][a] = { x: assets[a].x, y: assets[a].y }),
    );

    if (this.ws.socketOnline()) {
      this.ws.sendData({ request: 'set_layout', payload });
      this.setState({ changesSaved: true });
      setTimeout(() => {
        this.setState({ changesSaved: false });
      }, 5000);
    }
  };

  render() {
    const { classes } = this.props;
    const { assets, connections, loadedConnections } = this.state;

    // currently selected asset
    const selectedAsset = assets
      ? this.getAssetByKey(this.state.selectedAssetKey)
      : null;
    const progress =
      (loadedConnections * 100) / (Object.keys(connections).length || 100);

    // configure app's notifications:
    const snackbarOrigin = { vertical: 'bottom', horizontal: 'left' };
    const displayedSnackbars = {
      socketOffline: this.state.socketOffline,
      changesSaved: this.state.changesSaved,
      layoutEmpty:
        !this.state.socketOffline && Object.keys(assets).length === 0,
    };

    return (
      <div className={classes.root}>
        <div className={classes.appFrame}>
          {/* Top-Navigation component */}
          <TopNav
            saveLayout={this.saveLayout}
            ambient={this.state.ambient}
            ambientRising={this.state.ambientRising}
            plays={this.state.plays}
            executePlay={this.executePlay}
            mainsStatus={!!this.state.mainsStatus}
            togglePower={this.changeWallpowerStatus}
          />

          {/* Main Canvas */}
          <main className={classes.content}>
            <div className={classes.toolbar} />
            {Object.keys(connections).length !== 0 && (
              <Progress completed={progress} />
            )}

            {/* Drawings */}
            <Stage ref="stage">
              <Canvas
                getAssetByKey={this.getAssetByKey}
                onPosChange={this.onPosChange}
                onElementSelection={this.onElementSelection}
                assets={assets}
                connections={connections}
                selectedAssetKey={this.state.selectedAssetKey}
              />
            </Stage>
            {/* RightMost Card -> Display Element Details */}
            {!!this.state.selectedAssetKey && (
              <AssetDetails
                asset={selectedAsset}
                changeStatus={this.changeAssetStatus}
              />
            )}
            {/* Bottom-Left corner pop-ups */}
            <Notifications
              anchorOrigin={snackbarOrigin}
              displayedSnackbars={displayedSnackbars}
            />
          </main>
        </div>
      </div>
    );
  }
}

App.propTypes = {
  classes: PropTypes.object,
};

export default withStyles(styles)(App);
