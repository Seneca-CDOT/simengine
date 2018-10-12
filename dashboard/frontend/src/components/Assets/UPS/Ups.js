
import React from 'react';
import { Text, Group, Path, Image, Rect } from 'react-konva';
import PropTypes from 'prop-types';

import ups_monitor from '../../../images/ups_monitor_2.png';
import c14 from '../../../images/c14.svg';
import Socket from '../common/Socket';

/**
 * Draw Ups graphics
 */
export default class Ups extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      color: 'grey',
      selectedSocketKey: -1,
      x: props.x?props.x:40,
      y: props.y?props.y:40,
      ups_monitor: null,
      c14: null
    };

    this.selectSocket = this.selectSocket.bind(this);
    this.inputSocketPos = {x: 254, y: 5};
  }

  componentDidMount() {
    const upsMonitorImg = new window.Image();
    const c14Img = new window.Image();

    upsMonitorImg.src = ups_monitor;
    upsMonitorImg.onload = () => {
      // setState will redraw layer
      // because "upsMonitorImg" property is changed
      this.setState({ ups_monitor: upsMonitorImg });
    };

    c14Img.src = c14;
    c14Img.onload = () => {
      // setState will redraw layer
      // because "c14Img" property is changed
      this.setState({ c14: c14Img });
    };

  }

  componentWillReceiveProps(nextProps) {
    this.setState({ x: nextProps.x, y: nextProps.y });
  }

  /** Notify Parent of Selection */
  handleClick = () => {
    this.refs.ups.setZIndex(100);
    this.props.onElementSelection(this.props.assetId, this.props.asset);
  };

  /** Notify top-lvl Component that PDU-Outlet was selected*/
  selectSocket = (ckey) => {
    this.setState({ selectedSocketKey: ckey });
    this.props.onElementSelection(ckey, this.props.asset.children[ckey]);
  }

  getOutputCoordinates = () => {

    let chidCoord = {};
    let x = 250 + this.state.c14.width*0.5;
    let y = 150 + this.state.c14.height*0.5;

    Object.keys(this.props.asset.children).forEach((key, i) => {
      chidCoord[key] = {x, y};
      x += 100;

      if (i == 4) {
        y += 100;
        x = 250;
      }
    });

    return chidCoord;
  }

  updateUpsPos = (s) => {
    const coord = {
      x: s.target.attrs.x,
      y: s.target.attrs.y,
      inputConnections: [
        {
          x: this.inputSocketPos.x + this.state.c14.width*0.5,
          y: this.inputSocketPos.y + this.state.c14.height*0.5,
        }
      ],
      outputConnections: this.getOutputCoordinates(),
    };

    this.setState(coord);
    this.props.onPosChange(this.props.assetId, coord);
  }

  render() {

    let sockets = [];
    const inputSocket = <Image image={this.state.c14} x={this.inputSocketPos.x} y={this.inputSocketPos.y}/>;

    const upsName = this.props.asset.name ? this.props.asset.name:'ups';
    let chargeBar = "|||||||||||||||||||||||||||||||||||";
    chargeBar = this.props.asset.battery === 1000 ? chargeBar: chargeBar.substring(chargeBar.length * (1-this.props.asset.battery * 0.001));

    const asset = this.props.asset;
    let y=10;
    let x=5;
    let socketIndex = 0;
    // Initialize outlets that are part of the device
    for (const ckey of Object.keys(asset.children)) {

      asset.children[ckey].name = `[${ckey}]`;
      sockets.push(
        <Socket
          y={y}
          x={x}
          key={ckey}
          onElementSelection={() => { this.selectSocket(ckey); }}
          selectable={true}
          draggable={false}
          asset={asset.children[ckey]}
          assetId={ckey}
          selected={this.state.selectedSocketKey === ckey && this.props.nestedComponentSelected}
          powered={this.props.asset.status !== 0}
          parentSelected={this.props.selected}
          hideName={true}
          onPosChange={this.props.onPosChange}
        />
      );
      x += 100;
      socketIndex++;
      if (socketIndex == 4) {
        y += 100;
        x = 5;
      }
    }


    return (
      <Group
        draggable="true"
        onDragMove={this.updateUpsPos.bind(this)}
        x={this.state.x}
        y={this.state.y}
        ref="ups"
      >


        {/* Draw Ups as SVG path */}
        <Path data={"M 51.551168,118.02771 H 161.85062 l 10.30629,7.10992 H 41.244884 Z M 41.225275,125.12154 H 172.17651 c 0.86917,0 1.56887,5.60194 1.56887,12.56046 v 86.52769 c 0,6.95848 -0.6997,12.56045 -1.56887,12.56045 H 41.225275 c -0.869151,0 -1.568866,-5.60197 -1.568866,-12.56045 V 137.682 c 0,-6.95852 0.699715,-12.56046 1.568866,-12.56046 z"}
          strokeWidth={0.4}
          stroke={this.props.selected ? 'blue' : 'grey'}
          fill={'white'}
          scale={{x: 4, y: 4}}
          y={-575}
          onClick={this.handleClick.bind(this)}
        />

        {/* UPS Output */}
        <Group
         x={250}
         y={130}
        >
          <Rect
            ref="rect"
            width="390"
            height="210"
            fill="white"
            stroke={this.props.selected ? 'blue' : 'grey'}
            strokeWidth={1.4}
          />
          {sockets}
        </Group>


        <Text y={-125} x={230} text={upsName} fontSize={18}  fontFamily={'Helvetica'} />

        {/* UPS Display */}
        <Group
          x={345}
          y={-50}
        >
          <Image
              image={this.state.ups_monitor}
              onClick={this.handleClick}
          />
          <Group y={50} x={18}>
            <Text
              text={`Output ${this.props.asset.status?'ON':'OFF'}`}
              fontFamily={'DSEG14Modern'}
              fontSize={16}
              fill={this.props.asset.status?'white':'grey'}
            />

            <Text y={30}
              text={`Batt ${Math.floor(this.props.asset.battery/10)}%`}
              fontFamily={'DSEG14Modern'}
              fontSize={16}
              fill={this.props.asset.status?'white':'grey'}
            />
            <Text y={30} x={110}
              text={chargeBar}

              fontSize={16}
              fill={this.props.asset.status?'white':'grey'}
            />
          </Group>
        </Group>

        {/* Input Socket */}
        {inputSocket}

      </Group>
    );
  }
}

Ups.propTypes = {
  name: PropTypes.string,
  x: PropTypes.number, // X position of the asset
  y: PropTypes.number, // Y position of the asset
  onPosChange: PropTypes.func.isRequired, // called on asset position change
  asset: PropTypes.object.isRequired, // Asset Details
  assetId: PropTypes.string.isRequired, // Asset Key
  selected: PropTypes.bool.isRequired, // Asset Selected by a user
  onElementSelection: PropTypes.func.isRequired, // Notify parent component of selection
  nestedComponentSelected: PropTypes.bool.isRequired, // One of the UPS outlets are selected
};
