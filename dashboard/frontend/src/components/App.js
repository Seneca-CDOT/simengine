import React, { Component } from 'react';
import { Stage, Layer, Line } from 'react-konva';
import gridBackground from '../images/grid.png';

// Material
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import { withStyles } from '@material-ui/core/styles';
import Snackbar from '@material-ui/core/Snackbar';
import Typography from '@material-ui/core/Typography';
import SettingsIcon from "@material-ui/icons/Settings";
import classNames from 'classnames';
import IconButton from '@material-ui/core/IconButton';
import Drawer from '@material-ui/core/Drawer';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Divider from '@material-ui/core/Divider';

// Local Components
import Pdu from './Assets/PDU/Pdu';
import Socket from './Assets/common/Socket';
import Server from './Assets/Server/Server';

import SimpleCard from './SimpleCard';
import initialState from './InitialState';

const drawerWidth = 240;

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

 class App extends Component {

  constructor() {
    super();

    this.state = {
      assets: initialState,
      selectedAssetKey: 0,
      connections:{},
      socketOffline: true,
      anchorEl: null
    };

    this.connectToSocket();
  }


  componentDidMount() {

    // Scale Layout on wheel event
    let stage = this.refs.stage.getStage();
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

  connectToSocket() {
    if ("WebSocket" in window)
    {
       console.log("WebSocket is supported by your Browser!");
       // Let us open a web socket
       this.ws = new WebSocket("ws://localhost:8000/simengine");
       this.ws.onopen = (() =>
       {
          // Web Socket is connected, send data using send()
          // this.ws.send("Hello server");
          // alert("Message is sent...");
          this.setState({ socketOffline: false });
       });
       this.ws.onmessage = ((evt) =>
       {
          const data = JSON.parse(evt.data);

          // Update state of the existing asset
          if('key' in data) {

            let assets = {...this.state.assets};

            if ((''+data.key).length === 5) {
              const parent_id = (''+data.key).substring(0, 4);
              let asset_details = {...assets[parent_id].children[data.key]};
              assets[parent_id].children[data.key] = {...asset_details, ...data.data};
            } else {
              let asset_details = {...assets[data.key]};
              assets[data.key] = {...asset_details, ...data.data};
            }

            this.setState({ assets });

          } else { // initial query
            let connections = {};

            Object.keys(data).map((k) => {
              let x1 = data[k].x?data[k].x:40;
              let y1 = data[k].y?data[k].y:0;
              if (data[k]['parent']) {

                for (const p of data[k]['parent']) {
                  const parent_key = (''+p.key).substring(0, 4);
                  let x = data[parent_key].x?data[parent_key].x:50;
                  let y = data[parent_key].y?data[parent_key].y:50;
                  connections[p.key] = {x, y, x1, y1, ckey: k };

                }
              }
            });

            this.setState({
              assets: data,
              connections
            });
          }

       }).bind(this);
       this.ws.onclose =  (() =>
       {
          // websocket is closed.
          // alert("Connection is closed...");
          this.setState({ socketOffline: true });
          setTimeout(() => {this.connectToSocket();}, 5000);
       }).bind(this);
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
      return this.state.assets[parent_key].children[key];
    } else {
      return this.state.assets[key];
    }
  }

  _update_wiring(asset, key, x, y) {
    let newConn = {};
    const connections = this.state.connections;

    if(asset['parent']) {

      for (const p of asset['parent']) {
        newConn[p.key] = {...connections[p.key], x1:x,  y1:y};
        x+=250;
      }
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

    let assets = {...this.state.assets};
    let asset_details = {...assets[key]};
    assets[key] = {...asset_details, ...{x: e.target.x(), y: e.target.y()}};

    if (asset.children) {
      let x=100;
      for (const ckey of Object.keys(asset.children)) {
        const c = this._update_wiring(this._get_asset_by_key(ckey), ckey, e.target.x()+x, e.target.y());
        Object.assign(childConn, c);
        x += 90;
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
    this.ws.send(JSON.stringify({request: 'power', key: assetKey, data }));
  }

  saveLayout() {
    let data = {};
    const assets = this.state.assets;
    Object.keys(assets).map((a) => ( data[a]= {x: assets[a].x, y: assets[a].y} ));
    this.ws.send(JSON.stringify({request: 'layout', data }));
  }

  handleMenu = event => {
    this.setState({ anchorEl: event.currentTarget });
  };

  handleClose = () => {
    this.setState({ anchorEl: null });
  };


  /** Add Socket to the Layout */
  drawSocket(key, asset) {
    const powered = asset.parent?this._get_asset_by_key(asset.parent[0].key).status:true;
    return (
    <Socket
      onPosChange={this.onPosChange.bind(this)}
      onElementSelection={this.onElementSelection.bind(this)}
      assetId={key}
      asset={asset}
      selectable={true}
      selected={this.state.selectedAssetKey === key}
      draggable={true}
      powered={powered}
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
      asset={asset}
      selected={this.state.selectedAssetKey === key}
      pduSocketSelected={this.state.selectedAssetKey in asset.children}
      powered={powered}
      x={asset.x}
      y={asset.y}
    />);
  }

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
      asset={asset}
      selected={this.state.selectedAssetKey === key}
      pduSocketSelected={this.state.selectedAssetKey in asset.children}
      powered={powered}
      x={asset.x}
      y={asset.y}
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
      if (assets[key].type == 'outlet' || assets[key].type === 'staticasset') {
        systemLayout.push(this.drawSocket(key, assets[key]));
      } else if (assets[key].type === 'pdu') {
        systemLayout.push(this.drawPdu(key, assets[key]));
      } else if (assets[key].type === 'server') {
        systemLayout.push(this.drawServer(key, assets[key]));
      }
    }

    // draw wires

    for (const key of Object.keys(connections)) {
      const socketX1pad = 34;
      const socketYpad = 35;
      let socketXpad = socketX1pad;
      const asset = this._get_asset_by_key(key);

      if (this.state.assets[connections[key].ckey].type == 'staticasset') {
        socketXpad = -35;
      }

      if (this.state.assets[connections[key].ckey].type == 'server') {
        socketXpad = -220;
      }

      wireDrawing.push(
        <Line
          points={[connections[key].x+socketX1pad , connections[key].y+socketYpad, connections[key].x1- socketXpad , connections[key].y1+socketYpad]}
          stroke={asset.status  === 1?"green":"grey"}
          strokeWidth={5}
        />
      );
    }

    const { anchorEl } = this.state;
    const open = Boolean(anchorEl);

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
              <div>
                <IconButton aria-owns={open ? 'menu-appbar' : null}
                    aria-haspopup="true"
                    color="inherit"
                    onClick={this.handleMenu}
                >
                <SettingsIcon/>
                </IconButton>
                  <Drawer open={open} onClose={this.handleClose}
                    classes={{paper: classes.drawerPaper,}} anchor={'left'}>
                    <div className={classes.toolbar}/>
                    <Divider />
                    <div
                      tabIndex={0}
                      role="button"
                      onClick={this.handleClose}
                      onKeyDown={this.handleClose}
                    >
                      <div className={classes.fullList}>
                        <List>
                          <ListItem button onClick={this.saveLayout.bind(this)}>
                            <ListItemText primary="Save Layout" />
                          </ListItem>
                        </List>
                      </div>
                    </div>
                </Drawer>
              </div>
            </Toolbar>
          </AppBar>

          {/* Main Canvas */}
          <main className={classes.content} style={{ backgroundImage: 'url('+gridBackground+')', backgroundRepeat: "repeat" }}>
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
            <Snackbar
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'left',
              }}
              open={this.state.socketOffline}
              ContentProps={{
                'aria-describedby': 'message-id',
              }}
              message={<span id="message-id">Socket is unavailable: trying to reconnect...</span>}
            />
          </main>
        </div>
      </div>
    );
  }
}

export default withStyles(styles)(App);
