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
      changesSaved: false,
      anchorEl: null
    };

    this.connectToSocket();
  }


  componentDidMount() {

    /////// Scale Layout on wheel event //////////
    let stage = this.refs.stage.getStage();
    stage.scale({ x: 0.7, y: 0.7 });
    stage.position({x: window.innerWidth * 0.3, y: window.innerHeight * 0.3 });

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

    ////////// Move canvas on middle mouse button down ///////////
    const moveCanvas = (e) => {
      e.preventDefault();
        const newPos = {
          x: (stage.x() + e.movementX),
          y: (stage.y() + e.movementY),
      };
      stage.position(newPos);
      stage.batchDraw();
    };

    window.addEventListener("mousedown", (e) => {
      if (e.button == 1) {
        e.preventDefault();
        window.addEventListener("mousemove", moveCanvas);
      }
    });

    window.addEventListener("mouseup", (e) => {
      if (e.button == 1) {
        e.preventDefault();
        window.removeEventListener("mousemove", moveCanvas);
      }
    });
  }

  connectToSocket() {
    if ("WebSocket" in window)
    {
       console.log("WebSocket is supported by your Browser!");
       // Let us open a web socket
       let new_uri = '';
       let loc = window.location;
       if (loc.protocol === "https:") {
          new_uri = "wss:";
       } else {
          new_uri = "ws:";
       }
       new_uri += "//" + loc.hostname + ':8000/simengine';
       this.ws = new WebSocket(new_uri);
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
          // console.log(data)
          // Update state of the existing asset
          if('key' in data) {

            let assets = {...this.state.assets};
            const isComponent = !this.state.assets[data.key];

            if (isComponent) {
              const parent_id = this._get_parent_key(data.key);
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
              let x1_pad = 0;
              if (data[k]['parent']) {
                for (const p of data[k]['parent']) {
                  const isComponent = !data[p.key];

                  let x = 0;
                  let y = 0;
                  if (isComponent) {
                    const parent_key = this._get_parent_key(p.key);
                    x = data[parent_key].children[p.key].x;
                    y = data[parent_key].children[p.key].y;
                  } else {
                    x = data[p.key].x?data[p.key].x:50;
                    y = data[p.key].y?data[p.key].y:50;
                  }

                  connections[p.key] = {x, y, x1: x1+x1_pad, y1, ckey: k };
                  x1_pad+=250;
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
    const {assets, connections} = this.state;
    Object.keys(assets).map((a) => ( data[a]= {x: assets[a].x, y: assets[a].y} ));

    Object.keys(connections).map((a) => {
      if (!assets[a]) {
        data[a]= { x: connections[a].x, y: connections[a].y };
      }
    });

    if (this.ws.readyState == this.ws.OPEN) {
      this.ws.send(JSON.stringify({request: 'layout', data }));
      this.setState({ changesSaved: true });
    }
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
      } else if (assets[key].type === 'server' || assets[key].type === 'serverwithbmc') {
        systemLayout.push(this.drawServer(key, assets[key]));
      }
    }

    // draw wires
    for (const key of Object.keys(connections)) {
      const socketX1pad = 34;
      const socketYpad = 35;
      let socketXpad = socketX1pad;
      const asset = this._get_asset_by_key(key);
      const child_type = this.state.assets[connections[key].ckey].type;

      if (child_type == 'staticasset') {
        socketXpad = -35;
      }

      if (child_type == 'server' || child_type === 'serverwithbmc') {
        socketXpad = -220;
      }

      wireDrawing.push(
        <Line
          points={[connections[key].x+socketX1pad , connections[key].y+socketYpad, connections[key].x1- socketXpad , connections[key].y1+socketYpad]}
          stroke={asset.status  === 1?"green":"grey"}
          strokeWidth={5}
          zIndex={300}
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
            {/* Display message if backend is not available */}
            <Snackbar
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'left',
              }}
              open={this.state.socketOffline}
              ContentProps={{
                'aria-describedby': 'socket-id',
              }}
              message={<span id="socket-id">Socket is unavailable: trying to reconnect...</span>}
            />
            {/* 'Changes Applied' Message */}
            <Snackbar
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'left',
              }}
              open={this.state.changesSaved}
              onClose={()=>this.setState({changesSaved: false})}
              autoHideDuration={1500}
              ContentProps={{
                'aria-describedby': 'message-id',
              }}
              message={<span id="message-id">Changes saved!</span>}
            />
          </main>
        </div>
      </div>
    );
  }
}

export default withStyles(styles)(App);
